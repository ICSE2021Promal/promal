#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import gensim
import io
import json
from keras import backend as K
from keras.preprocessing.sequence import pad_sequences
import numpy as np
import os
from PIL import Image
import string
import xml.etree.ElementTree as ET
from xml.dom.minidom import parse
import xml.dom.minidom


GPU_ID = '0'
os.environ['CUDA_VISIBLE_DEVICES'] = GPU_ID

parser = argparse.ArgumentParser(description='pre-processing groundtruth data.')
parser.add_argument('--data_dir', type=str, required=True,
    help='path to pre-processed training data for pre-training')
parser.add_argument('--groundtruth_dir', type=str, required=True,
    help='path to rendering result of apps')
parser.add_argument('--output_dir', type=str, required=True,
    help='path to directory to save the pre-processed numpys')
args = parser.parse_args()

model = gensim.models.Word2Vec.load(args.data_dir + '/word2vec_wx')
# part 1: get uitree!
def get_image(img):
    try:
        im = Image.open(img).convert('RGB') 
        new_img = im.resize((90, 160), Image.BILINEAR)
        data = np.array(new_img)
        return data
    except IOError:
        a = np.zeros([160, 90, 3], dtype='float32')
        return a

def get_other(bounds):
    x = int(bounds.split(',')[0][1:])
    y = int(bounds.split(',')[1].split('][')[0])
    width = int(bounds.split(',')[1].split('][')[1]) - x
    height = int(bounds.split(',')[2][:-1]) - y
    return x, y, width, height

def get_text(text):
    total = np.zeros(shape=(256,), dtype='float32')
    for c in string.punctuation:
        text = text.replace(c, " ")
    totalnum = 0
    if text != '' or text != 'Torchlight' or text in model:
        textlist = text.split(" ")
        totalnum = len(textlist)
        for eachword in textlist:
            if eachword not in model:
                totalnum -= 1
                continue
            total += model[eachword]
        if totalnum > 0:
            total = total / len(textlist)
    return total, totalnum

def get_tags(widget):
    total_text = np.zeros(shape=(256,), dtype='float32')
    total_cnt = 0
    total_other = []
    total_tag = ""
    text, cnt = get_text(widget.attrib['text'])
    x, y, w, h = get_other(widget.attrib['bounds'])
    other = [x, y, w, h]
    tag = widget.attrib['class'].split('.')[-1]
    childnum = len(widget)
    if childnum == 0:
        total_tag += (" " + tag + " ")
        total_text += cnt * text
        total_cnt += cnt
        total_other.append(other)
        if total_cnt > 1:
            total_text /= total_cnt
        return total_cnt, total_text, total_other, total_tag
    mid = childnum // 2
    for i in range(mid + 1):
        tmp_cnt, tmp_text, tmp_other, tmp_tree = get_tags(widget[i])
        total_text += tmp_cnt * tmp_text
        total_cnt += tmp_cnt
        total_other.extend(tmp_other)
        total_tag += tmp_tree
    total_tag += (" " + tag + " ")
    total_text += cnt * text
    total_cnt += cnt
    total_other.append(other)
    for i in range(mid + 1, childnum):
        tmp_cnt, tmp_text, tmp_other, tmp_tree = get_tags(widget[i])
        total_text += tmp_cnt * tmp_text
        total_cnt += tmp_cnt
        total_other.extend(tmp_other)
        total_tag += tmp_tree
    if total_cnt > 1:
        total_text /= total_cnt
    return total_cnt, total_text, total_other, total_tag 

all_tags_dict = json.load(open("./all_tags_dict.json", 'r'))

def crop_image(img, x, y, width, height):
    try:
        im = Image.open(img).convert('RGB')
        data = np.array(im)
        for i in range(800):
            for j in range(480):
                if i < x  or i >= (x + width):
                    if j < y  or j >= (y + height):
                        data[i][j][0] = data[i][j][1] = data[i][j][2] = 0
        img = Image.fromarray(data).convert('RGB')
        img = img.resize((90, 160), Image.BILINEAR)
        data = np.array(img)
        return data
    except IOError:
        a = np.zeros([160, 90, 3], dtype='float32')
        return a

# part 2: read groundtruth files
# train data and test data
def is_widget(x, y, widgetname):
    bounds = widgetname.split(":")[-1]
    lefts = bounds.split("][")[0].replace("[", '').split(',')
    rights = bounds.split("][")[1].replace("]", '').split(',')
    x1 = int(lefts[0])
    y1 = int(lefts[1])
    x2 = int(rights[0])
    y2 = int(rights[1])
    if x1 < float(x) < x2 and y1 < float(y) < y2:
        return True
    else:
        return False

groundtruth_path = args.groundtruth_dir + "/groundtruth/"
train_app_list = os.listdir(groundtruth_path)
activity_id, widget_id = 0, 0
image_list, uitree_list2, text_list, other_list = [], [], [], []
w_image_list, w_uitree_list, w_text_list, w_other_list = [], [], [], []
activity_list, widget_list = [], []

# get numpys for all windows and widgets in ground truth
for eachapp in train_app_list:
    if eachapp[0] == '.':
        continue
    xmllist = os.listdir(args.groundtruth_dir + "/XML/" + eachapp[:-4])
    for eachxml in xmllist:
        if eachxml[-4:] != ".xml":
            continue
        # widget information
        DOMTree = xml.dom.minidom.parse(args.groundtruth_dir + "/XML/" + eachapp[:-4] + "/" + eachxml)
        collection = DOMTree.documentElement
        for each in collection.getElementsByTagName("node"):
            resource_id = each.getAttribute('resource-id')
            wclass = each.getAttribute('class').split('.')[-1]
            text = each.getAttribute('text')
            bounds = each.getAttribute('bounds')
            x, y, width, height = get_other(bounds)
            total, cnt = get_text(text)
            img = crop_image(args.groundtruth_dir + "/Screenshot/" + eachapp[:-4] + "/" + eachxml[:-4] + ".png", 
                x, y, width, height)
            w_image_list.append(img)
            w_text_list.append(total)
            w_other_list.append([x, y, width, height])
            w_uitree_list.append(wclass)
            widget_list.append(eachapp[:-4] + "/"+ eachxml[:-4] + ": "+resource_id+": " + bounds)
        # activity information
        image_list.append(
            get_image(args.groundtruth_dir + "/Screenshot/" + eachapp[:-4] + "/" + eachxml[:-4] + ".png"))
        tree = ET.ElementTree(file=args.groundtruth_dir + "/XML/" + eachapp[:-4] + "/" + eachxml)
        root = tree.getroot()
        total_cnt, total_text, total_other, total_tag = get_tags(root[0])
        uitree_list2.append(total_tag)
        other_list.append(total_other)
        text_list.append(total_text)
        activity_list.append(eachapp[:-4] + "/"+ eachxml[:-4])
other_np = pad_sequences(np.array(other_list), maxlen=128, 
    dtype='float32', padding='post', truncating='pre')
np.save(args.output_dir + "image_np.npy", np.array(image_list))
np.save(args.output_dir + "other_np.npy", other_np)
np.save(args.output_dir + "text_np.npy", np.array(text_list))
np.save(args.output_dir + "w_image_np.npy", np.array(w_image_list))
np.save(args.output_dir + "w_other_np.npy", np.array(w_other_list))
np.save(args.output_dir + "w_text_np.npy", np.array(w_text_list))
np.save(args.output_dir + "activity_np.npy", np.array(activity_list))
np.save(args.output_dir + "widget_np.npy", np.array(widget_list))
tmp_np = np.array(uitree_list2)

t_tmp_np = []
for eachuitree in uitree_list2:
    ttt = []
    for eachtag in eachuitree:
        embedding = all_tags_dict.get(eachtag, None)
        if embedding is not None:
            ttt.append(embedding)
        else:
            ttt.append(all_tags_dict.get("unknown", None))
    t_tmp_np.append(ttt)
tmp_np = np.array(t_tmp_np)

uitree_np2 = pad_sequences(tmp_np, maxlen=256, dtype='float32', padding='post', truncating='pre')
np.save(args.output_dir + "uitree_np.npy", uitree_np2)
tmp_np = np.array(w_uitree_list)

t_tmp_np = []
for eachtag in tmp_np:
    embedding = all_tags_dict.get(eachtag, None)
    if embedding is not None:
        t_tmp_np.append(embedding)
    else:
        t_tmp_np.append(all_tags_dict.get("unknown", None))
tmp_np = np.array(t_tmp_np)

np.save(args.output_dir + "w_uitree_np.npy", tmp_np)
print("total activity num: ", len(activity_list))
print("total widget num: ", len(widget_list))
positive_pairs = []
for eachapp in train_app_list:
    if eachapp[0] == ".":
        continue
    f = open(groundtruth_path + eachapp, 'r')
    dict = {}
    try:
        while True:
            line = f.readline()
            parse = line.split("\\n")
            if len(parse) == 1:
                break
            if len(parse) != 11:
                continue
            source = parse[-2]
            target = parse[-1][:-1]
            if parse[2] == "back" or parse[2] == "menu" or parse[2] == "launch":
                continue
            source_widget_index = -1
            idx = 0
            for eachwidget in widget_list:
                if eachwidget.split(": ")[0] == eachapp[:-4] + "/" + source:
                    if is_widget(parse[-4], parse[-3], eachwidget):
                        source_widget_index = idx
                idx += 1
            if source_widget_index == -1:
                print(parse[2], parse[-4], parse[-3], "not found")
                continue
            target_activity_name = eachapp[:-4] + "/" + target
            positive_pairs.append([source_widget_index, activity_list.index(target_activity_name)])
    finally:
        f.close()

np.save(args.output_dir + "/positive_pairs.npy", np.array(positive_pairs))

# get 10-fold training data from groundtruth
image_list, uitree_list2, text_list, other_list = [], [], [], []
w_image_list, w_uitree_list, w_text_list, w_other_list = [], [], [], []
activity_index_list, widget_index_list = [], []
app_list = os.listdir(groundtruth_path)
for i in range(10):
    train_app_list = []
    test_app_list = []
    for j in range(len(os.list(args.groundtruth_dir + "XML/"))):
        if j % 10 != i:
            train_app_list.append(app_list[j][:-4])
        else:
            test_app_list.append(app_list[j][:-4])
    activity_id, widget_id = 0, 0
    image_list, uitree_list2, text_list, other_list = [], [], [], []
    w_image_list, w_uitree_list, w_text_list, w_other_list = [], [], [], []
    activity_id_list, widget_id_list = [], []
    # training data set
    for eachapp in train_app_list:
        xmllist = os.listdir(args.groundtruth_dir + "/XML/" + eachapp)
        for eachxml in xmllist:
            if eachxml[-4:] != ".xml":
                continue
            # widget information
            DOMTree = xml.dom.minidom.parse(args.groundtruth_dir + "/XML/" + eachapp + "/" + eachxml)
            collection = DOMTree.documentElement
            for each in collection.getElementsByTagName("node"):
                resource_id = each.getAttribute('resource-id')
                wclass = each.getAttribute('class').split('.')[-1]
                text = each.getAttribute('text')
                bounds = each.getAttribute('bounds')
                x, y, width, height = get_other(bounds)
                total, cnt = get_text(text)
                img = crop_image(args.groundtruth_dir + "/Screenshot/" + eachapp + "/" + eachxml[:-4] + ".png", x, y, width, height)
                w_image_list.append(img)
                w_text_list.append(total)
                w_other_list.append([x, y, width, height])
                w_uitree_list.append(wclass)
                widget_id_list.append(widget_list.index(eachapp + "/" + eachxml[:-4] + ": " +resource_id+": "+ bounds))
            # activity information
            image_list.append(
                get_image(args.groundtruth_dir + "/Screenshot/" + eachapp + "/" + eachxml[:-4] + ".png"))
            tree = ET.ElementTree(file=args.groundtruth_dir + "/XML/" + eachapp + "/" + eachxml)
            root = tree.getroot()
            total_cnt, total_text, total_other, total_tag = get_tags(root[0])
            uitree_list2.append(total_tag)
            other_list.append(total_other)
            text_list.append(total_text)
            activity_id_list.append(activity_list.index(eachapp + "/" + eachxml[:-4]))
    other_np = pad_sequences(np.array(other_list), maxlen=128, dtype='float32', padding='post', truncating='pre')
    np.save(args.output_dir + "image_np_tr" + str(i) + ".npy", np.array(image_list))
    np.save(args.output_dir + "other_np_tr" + str(i) + ".npy", other_np)
    np.save(args.output_dir + "text_np_tr" + str(i) + ".npy", np.array(text_list))
    np.save(args.output_dir + "w_image_np_tr" + str(i) + ".npy", np.array(w_image_list))
    np.save(args.output_dir + "w_other_np_tr" + str(i) + ".npy", np.array(w_other_list))
    np.save(args.output_dir + "w_text_np_tr" + str(i) + ".npy", np.array(w_text_list))
    np.save(args.output_dir + "activity_id_tr" + str(i) + ".npy", np.array(activity_id_list))
    np.save(args.output_dir + "widget_id_tr" + str(i) + ".npy", np.array(widget_id_list))
    del activity_id_list, widget_id_list
    del image_list, other_list, text_list, w_image_list, w_other_list, w_text_list

    # test data set
    activity_id_t, widget_id_t = 0, 0
    image_list_t, uitree_list_t, text_list_t, other_list_t = [], [], [], []
    w_image_list_t, w_uitree_list_t, w_text_list_t, w_other_list_t = [], [], [], []
    activity_list_t, widget_list_t = [], []
    activity_id_list_t, widget_id_list_t = [], []
    for eachapp in test_app_list:
        xmllist = os.listdir(args.groundtruth_dir + "/XML/" + eachapp)
        for eachxml in xmllist:
            # widget information
            DOMTree = xml.dom.minidom.parse(args.groundtruth_dir + "/XML/" + eachapp + "/" + eachxml)
            collection = DOMTree.documentElement
            for each in collection.getElementsByTagName("node"):
                resource_id = each.getAttribute('resource-id')
                wclass = each.getAttribute('class').split('.')[-1]
                text = each.getAttribute('text')
                bounds = each.getAttribute('bounds')
                x, y, width, height = get_other(bounds)
                total, cnt = get_text(text)
                img = crop_image(args.groundtruth_dir + "/XML/" + eachapp + "/" + eachxml[:-4] + ".png", 
                    x, y, width, height)
                w_image_list_t.append(img)
                w_text_list_t.append(total)
                w_other_list_t.append([x, y, width, height])
                w_uitree_list_t.append(wclass)
                widget_id_list_t.append(eachapp + "/" + eachxml[:-4] + ": " +resource_id+": "+ bounds)
            # activity information
            image_list_t.append(
                get_image(args.groundtruth_dir + "/Screenshot/" + eachapp + "/" + eachxml[:-4] + ".png"))
            tree = ET.ElementTree(file=args.groundtruth_dir + "/XML/" + eachapp + "/" + eachxml)
            root = tree.getroot()
            total_cnt, total_text, total_other, total_tag = get_tags(root[0])
            uitree_list_t.append(total_tag)
            other_list_t.append(total_other)
            text_list_t.append(total_text)
            activity_list_t.append(eachapp + "/" + eachxml)
            activity_id_list_t.append(eachapp + "/" + eachxml[:-4])
    other_np = pad_sequences(np.array(other_list_t), maxlen=128, dtype='float32', 
        padding='post', truncating='pre')
    np.save(args.output_dir + "image_np_t" + str(i) + ".npy", np.array(image_list_t))
    np.save(args.output_dir + "other_np_t" + str(i) + ".npy", other_np)
    np.save(args.output_dir + "text_np_t" + str(i) + ".npy", np.array(text_list_t))
    np.save(args.output_dir + "w_image_np_t" + str(i) + ".npy", np.array(w_image_list_t))
    np.save(args.output_dir + "w_other_np_t" + str(i) + ".npy", np.array(w_other_list_t))
    np.save(args.output_dir + "w_text_np_t" + str(i) + ".npy", np.array(w_text_list_t))
    np.save(args.output_dir + "activity_id_t" + str(i) + ".npy", np.array(activity_id_list_t))
    np.save(args.output_dir + "widget_id_t" + str(i) + ".npy", np.array(widget_id_list_t))
    del activity_id_list_t, widget_id_list_t
    del image_list_t, other_list_t, text_list_t, 
    del w_image_list_t, w_other_list_t, w_text_list_t
    
    t_tmp_np = []
    for eachuitree in uitree_list2:
        ttt = []
        for eachtag in eachuitree:
            embedding = all_tags_dict.get(eachtag, None)
            if embedding is not None:
                ttt.append(embedding)
            else:
                ttt.append(all_tags_dict.get("unknown", None))
        t_tmp_np.append(ttt)
    tmp_np = np.array(t_tmp_np)
    uitree_np2 = pad_sequences(tmp_np, maxlen=256, dtype='float32', 
        padding='post', truncating='pre')
    np.save(args.output_dir + "uitree_np_tr" + str(i) + ".npy", uitree_np2)

    t_tmp_np = []
    for eachuitree in uitree_list_t:
        ttt = []
        for eachtag in eachuitree:
            embedding = all_tags_dict.get(eachtag, None)
            if embedding is not None:
                t_tmp_np.append(embedding)
            else:
                t_tmp_np.append(all_tags_dict.get("unknown", None))
        t_tmp_np.append(ttt)
    tmp_np = np.array(t_tmp_np)
    uitree_np_t = pad_sequences(tmp_np, maxlen=256, dtype='float32', 
        padding='post', truncating='pre')
    np.save(args.output_dir + "uitree_np_t" + str(i) + ".npy", uitree_np_t)

    tmp_np = np.array(w_uitree_list)

    t_tmp_np = []
    for eachtag in tmp_np:
        embedding = all_tags_dict.get(eachtag, None)
        if embedding is not None:
            t_tmp_np.append(embedding)
        else:
            t_tmp_np.append(all_tags_dict.get("unknown", None))
    tmp_np = np.array(t_tmp_np)
    np.save(args.output_dir + "w_uitree_np_tr" + str(i) + ".npy", tmp_np)
    tmp_np = np.array(w_uitree_list_t)

    t_tmp_np = []
    for eachtag in tmp_np:
        embedding = all_tags_dict.get(eachtag, None)
        if embedding is not None:
            t_tmp_np.append(embedding)
        else:
            t_tmp_np.append(all_tags_dict.get("unknown", None))
    tmp_np = np.array(t_tmp_np)
    np.save(args.output_dir + "w_uitree_np_t" + str(i) + ".npy", tmp_np)
    del uitree_list2, uitree_list_t, uitree_np_t, w_uitree_list, w_uitree_list_t, tmp_np
    
    # get positive pairs in groundtruth
    positive_pairs = []
    for eachapp in train_app_list:
        f = open(groundtruth_path + eachapp + ".dot", 'r')
        try:
            while True:
                line = f.readline()
                parse = line.split("\\n")
                if len(parse) == 1:
                    break
                if len(parse) != 7:
                    continue
                source = parse[-2]
                target = parse[-1][:-1]
                if parse[2] == "back" or parse[2] == "menu" or parse[2] == "lauch":
                    continue
                source_widget_index = -1
                idx = 0
                for eachwidget in widget_list:
                    if eachwidget.split(":")[0] == eachapp + "/" + source:
                        if is_widget(parse[3], parse[4], eachwidget):
                            source_widget_index = idx
                    idx += 1
                if source_widget_index == -1:
                    print(parse[2], parse[3], parse[4], "not found")
                    continue
                target_activity_name = eachapp + "/" + target
                positive_pairs.append([source_widget_index, 
                    activity_list.index(target_activity_name)])
        finally:
            f.close()

    np.save(args.output_dir + "positive_pairs" + str(i) + ".npy",
        np.array(positive_pairs))

    positive_pairs_t = []
    for eachapp in test_app_list:
        f = open(groundtruth_path + eachapp + ".dot", 'r')
        try:
            while True:
                line = f.readline()
                parse = line.split("\\n")
                if len(parse) == 1:
                    break
                if len(parse) != 11:
                    continue
                source = parse[-2]
                target = parse[-1][:-1]
                if parse[2] == "back" or parse[2] == "menu" or parse[2] == "lauch":
                    continue
                source_widget_index = -1
                idx = 0
                for eachwidget in widget_list:
                    if eachwidget.split(":")[0] == eachapp + "/" + source:
                        if is_widget(parse[-4], parse[-3], eachwidget):
                            source_widget_index = idx
                    idx += 1
                if source_widget_index == -1:
                    print(parse[2], parse[-4], parse[-3], "not found")
                    continue
                target_activity_name = eachapp + "/" + target
                positive_pairs_t.append([source_widget_index, activity_list.index(target_activity_name)])
        finally:
            f.close()
    np.save(args.output_dir + "positive_pairs_t" + str(i) + ".npy",
            np.array(positive_pairs_t))
