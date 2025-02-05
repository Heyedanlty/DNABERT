# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors and The HuggingFace Inc. team.
# Copyright (c) 2018, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
    from scipy.stats import pearsonr, spearmanr
    import numpy as np
    from sklearn.metrics import matthews_corrcoef, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score

    _has_sklearn = True
except (AttributeError, ImportError):
    _has_sklearn = False


def is_sklearn_available():
    return _has_sklearn


if _has_sklearn:

    def simple_accuracy(preds, labels):
        return (preds == labels).mean()

    def acc_and_f1(preds, labels):
        acc = simple_accuracy(preds, labels)
        f1 = f1_score(y_true=labels, y_pred=preds)
        return {
            "acc": acc,
            "f1": f1,
            "acc_and_f1": (acc + f1) / 2,
        }
    
    def acc_f1_mcc(preds, labels):
        acc = simple_accuracy(preds, labels)
        f1 = f1_score(y_true=labels, y_pred=preds)
        mcc = matthews_corrcoef(labels, preds)
        return {
            "acc": acc,
            "f1": f1,
            "mcc": mcc
        }

    def acc_f1_mcc_auc_aupr_pre_rec(preds, labels, probs):
        acc = simple_accuracy(preds, labels)
        precision = precision_score(y_true=labels, y_pred=preds)
        recall = recall_score(y_true=labels, y_pred=preds)
        f1 = f1_score(y_true=labels, y_pred=preds)
        mcc = matthews_corrcoef(labels, preds)
        auc = roc_auc_score(labels, probs)
        aupr = average_precision_score(labels, probs)
        return {
            "acc": acc,
            "f1": f1,
            "mcc": mcc,
            "auc": auc,
            "aupr": aupr,
            "precision": precision,
            "recall": recall,
        }

    def acc_f1_mcc_auc_pre_rec(preds, labels, probs):
        acc = simple_accuracy(preds, labels)
        precision = precision_score(y_true=labels, y_pred=preds, average="macro")
        recall = recall_score(y_true=labels, y_pred=preds, average="macro")
        f1 = f1_score(y_true=labels, y_pred=preds, average="macro")
        mcc = matthews_corrcoef(labels, preds)
        auc = roc_auc_score(labels, probs, average="macro", multi_class="ovo")
        return {
            "acc": acc,
            "f1": f1,
            "mcc": mcc,
            "auc": auc,
            "precision": precision,
            "recall": recall,
        }

    def pearson_and_spearman(preds, labels):
        pearson_corr = pearsonr(preds, labels)[0]
        spearman_corr = spearmanr(preds, labels)[0]
        return {
            "pearson": pearson_corr,
            "spearmanr": spearman_corr,
            "corr": (pearson_corr + spearman_corr) / 2,
        }
    
    def acc_f1_mcc_auc_pre_rec_forMultiLabel(preds, labels, probs):
        from collections import defaultdict
        import math
        
        def self_acc_f1_pre_rec(y_true, y_pred):
            num_batch = len(y_true)
            num_labels = len(y_true[0])
            confusion_matrix = [defaultdict(int) for i in range(num_labels)]
            for i in range(num_batch):
                for j in range(num_labels):
                    if y_true[i][j] == 2 or y_true[i][j] == 3:
                        # only evaluate if the original label is true, not overlapping is true
                        # skip those positive samples generated by overlapping
                        continue
                    if y_true[i][j] and y_pred[i][j]:
                        confusion_matrix[j]["TP"] += 1
                    elif y_true[i][j] and not y_pred[i][j]:
                        confusion_matrix[j]["FN"] += 1
                    elif not y_true[i][j] and y_pred[i][j]:
                        confusion_matrix[j]["FP"] += 1
                    else:
                        confusion_matrix[j]["TN"] += 1
            ret = [None for i in range(num_labels)]
            for i in range(num_labels):
                TP = confusion_matrix[i]["TP"]
                FP = confusion_matrix[i]["FP"]
                TN = confusion_matrix[i]["TN"]
                FN = confusion_matrix[i]["FN"]
                #print(TP, FP, TN, FN)
                print(i, TP, FP, FN, TN, TP+FP, TP+FN, TP+TN)
                precision = TP / (TP + FP) if (TP + FP) != 0 else (1.0 if (TP + FN) == 0 else 0.0)
                recall = TP / (TP + FN) if (TP + FN) != 0 else 1
                f1 = 2 * precision * recall / (precision + recall) if not math.isclose(precision + recall, 0) else 0.0
                accuracy = (TP + TN) / (TP + TN + FP + FN)
                ret[i] = {
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "accuracy": accuracy,
                }
            return ret

        tmp = self_acc_f1_pre_rec(y_true=labels, y_pred=preds)
        num_labels = len(preds[0])

        ret = dict()
        for i in range(num_labels):
            # calculate auc
            if i == 0:
                labels_auc = np.array(labels)[:,i]
                probs_auc = np.array(probs)[:,i]
            else:
                labels_auc = []
                probs_auc = []
                for j in range(len(preds)):
                    if labels[j][i] == 2 or labels[j][i] == 3:
                        continue
                    else:
                        labels_auc.append(labels[j][i])
                        probs_auc.append(probs[j][i])
                labels_auc = np.array(labels_auc)
                probs_auc = np.array(probs_auc)            
            try:
                #auc = roc_auc_score(labels_, probs_, average="macro", multi_class="ovo")
                auc = roc_auc_score(labels_auc, probs_auc, average=None)
            except:
                #print(f"{i} label is not balanced!")
                auc = 0.0

            acc = tmp[i]["accuracy"]
            f1 = tmp[i]["f1"]
            precision = tmp[i]["precision"]
            recall = tmp[i]["recall"]
            ret[i] = {
                "acc": acc,
                "auc": auc,                
                "f1": f1,
                "precision": precision,
                "recall": recall
            }
        ret[num_labels] = {
            "acc" : sum([ret[i]["acc"] for i in range(1,num_labels)]) / (num_labels - 1),
            "auc" : sum([ret[i]["auc"] for i in range(1, num_labels)]) / (num_labels - 1),
            "f1": sum([ret[i]["f1"] for i in range(1, num_labels)]) / (num_labels - 1),
            "precision" : sum([ret[i]["precision"] for i in range(1, num_labels)]) / (num_labels - 1),
            "recall" : sum([ret[i]["recall"] for i in range(1, num_labels)]) / (num_labels - 1),
        }
        ans = defaultdict(list)
        for i in range(num_labels):
            for k in ret[i]:
                ans[k].append(ret[i][k])
        for k in ans:
            ans[k] = np.array(ans[k])
        return ans, ret[num_labels] # average


    def glue_compute_metrics(task_name, preds, labels, probs=None):
        assert len(preds) == len(labels)
        if task_name == "cola":
            return {"mcc": matthews_corrcoef(labels, preds)}
        elif task_name == "sst-2":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name in ["dna690", "dnapair"]:
            return acc_f1_mcc_auc_aupr_pre_rec(preds, labels, probs)
        elif task_name == "dnaprom" or task_name == "dnasingleenhancer":
            return acc_f1_mcc_auc_pre_rec(preds, labels, probs)
            # return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "dnasplice":
            return acc_f1_mcc_auc_pre_rec(preds, labels, probs)
        elif task_name == "mrpc":
            return acc_and_f1(preds, labels)
        elif task_name == "sts-b":
            return pearson_and_spearman(preds, labels)
        elif task_name == "qqp":
            return acc_and_f1(preds, labels)
        elif task_name == "mnli":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "mnli-mm":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "qnli":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "rte":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "wnli":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "hans":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "dnaenhancer":
            return acc_f1_mcc_auc_pre_rec_forMultiLabel(preds, labels, probs)
        else:
            raise KeyError(task_name)

    def xnli_compute_metrics(task_name, preds, labels):
        assert len(preds) == len(labels)
        if task_name == "xnli":
            return {"acc": simple_accuracy(preds, labels)}
        else:
            raise KeyError(task_name)
