# Qwen-v9-C：逐轮目的、修改与结果

本页逐轮转录已归档值，不重新评分、不运行模型。共30个完整候选；不是新增30次实验。研究者当时的理由按原文保留，其中预期不能读作已验证结果。每轮均从其记录指定的基线和父候选解释，不能默认累加补丁。

原始完整档案（含逐题答案）：

- [experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/C-evaluations-and-candidates.json.gz](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/C-evaluations-and-candidates.json.gz)

## 第1轮

**当时目的与操作理由（原文）**

Diagnostic causal localization: attenuate the largest layer-19 head contribution to the failure-by-wording interaction, without assigning a semantic function from its ID.

**本轮原记录的主分数**：`0.58984375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-ffc4d6e2a1b29f3ada56cf2c3c56d7ca7b2d702f9e94cf3bb693c6cc654a7655",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.58984375
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 327680,
  "id": "c-ffc4d6e2a1b29f3ada56cf2c3c56d7ca7b2d702f9e94cf3bb693c6cc654a7655",
  "l2": 6.17962786093203,
  "parent": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "rationale": "Diagnostic causal localization: attenuate the largest layer-19 head contribution to the failure-by-wording interaction, without assigning a semantic function from its ID.",
  "tensors": {
    "model.language_model.layers.19.self_attn.o_proj.weight": {
      "base_sha256": "7918d2af0fa2f082d00dc4ed0f1f3eb05da6e474592694c0f8f2b677f4e798e7",
      "changed": 327680,
      "content_sha256": "9932a1ca22d53bc8988b48bd857fbcbfe359a013c03c26e4f156a9548643abf9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "02c69f59e3832701f465fb692ea9b19bb8bbc7c752d2d623d2b3c8ceee2fff36.npz",
      "sha256": "a728e528613e5d31c773bee987c1507f95e8ce2ed5b3bde9167d669b7aaceb95",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 327680
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-ffc4d6e2a1b29f3ada56cf2c3c56d7ca7b2d702f9e94cf3bb693c6cc654a7655",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.884375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 46,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 41,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 59,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 37,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 63,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58984375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第2轮

**当时目的与操作理由（原文）**

Stronger causal dose for the weakly supported layer-19 head-31 harmful-write hypothesis; absolute edit against W0, not cumulative half attenuation.

**本轮原记录的主分数**：`0.58203125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:1:counterfact_usual"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 327680,
  "id": "c-62fefa5231c53dedb33c8e6c47e01c671a9345ddbafdfc69e9672431ccb9266d",
  "l2": 12.35925572186406,
  "parent": "c-ffc4d6e2a1b29f3ada56cf2c3c56d7ca7b2d702f9e94cf3bb693c6cc654a7655",
  "rationale": "Stronger causal dose for the weakly supported layer-19 head-31 harmful-write hypothesis; absolute edit against W0, not cumulative half attenuation.",
  "tensors": {
    "model.language_model.layers.19.self_attn.o_proj.weight": {
      "base_sha256": "7918d2af0fa2f082d00dc4ed0f1f3eb05da6e474592694c0f8f2b677f4e798e7",
      "changed": 327680,
      "content_sha256": "fc6552ae3861a1f8e4972ae27895d6cf6304c7f5a37096002ed2fbee1bdf9ca6",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "02c69f59e3832701f465fb692ea9b19bb8bbc7c752d2d623d2b3c8ceee2fff36.npz",
      "sha256": "f70634ae82223e853719aa9c3f50f4ac7bd387c523994987a0bf04d3e27e86ac",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 327680
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-62fefa5231c53dedb33c8e6c47e01c671a9345ddbafdfc69e9672431ccb9266d",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.874609375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 59,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 45,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 41,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 42,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 41,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 34,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 63,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 56,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 45,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 54,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 63,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.71875,
    "repair_score": 0.58203125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第3轮

**当时目的与操作理由（原文）**

Opposite-sign, support- and norm-matched causal control for the head-19.31 attenuation hypothesis.

**本轮原记录的主分数**：`0.5859375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 327680,
  "id": "c-871b2d385216931fbed86a24b4de8dbc0effc34f128b7269aa59d63a413599fa",
  "l2": 6.179591565111615,
  "parent": "c-62fefa5231c53dedb33c8e6c47e01c671a9345ddbafdfc69e9672431ccb9266d",
  "rationale": "Opposite-sign, support- and norm-matched causal control for the head-19.31 attenuation hypothesis.",
  "tensors": {
    "model.language_model.layers.19.self_attn.o_proj.weight": {
      "base_sha256": "7918d2af0fa2f082d00dc4ed0f1f3eb05da6e474592694c0f8f2b677f4e798e7",
      "changed": 327680,
      "content_sha256": "5c69208ddab1c956ebbff84332700e3afd9fddd5ffabf2eb97d6694bd78fecd0",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "02c69f59e3832701f465fb692ea9b19bb8bbc7c752d2d623d2b3c8ceee2fff36.npz",
      "sha256": "7bc01e08a69b069e42c91bb049de48b80cc5adc701d1267175375dd8037dff68",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 327680
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-871b2d385216931fbed86a24b4de8dbc0effc34f128b7269aa59d63a413599fa",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.887890625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 42,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.765625,
    "repair_score": 0.5859375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第4轮

**当时目的与操作理由（原文）**

Uniform random-head control for head-selection specificity after opposite-sign head31 intervention contradicted a simple harmful-write interpretation.

**本轮原记录的主分数**：`0.58203125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 327680,
  "id": "c-8c7f139cfe1801ba1614bc353a8ec3101b4925791c39caed18924b8cf8a2a4e8",
  "l2": 6.179540835997721,
  "parent": "c-871b2d385216931fbed86a24b4de8dbc0effc34f128b7269aa59d63a413599fa",
  "rationale": "Uniform random-head control for head-selection specificity after opposite-sign head31 intervention contradicted a simple harmful-write interpretation.",
  "tensors": {
    "model.language_model.layers.19.self_attn.o_proj.weight": {
      "base_sha256": "7918d2af0fa2f082d00dc4ed0f1f3eb05da6e474592694c0f8f2b677f4e798e7",
      "changed": 327680,
      "content_sha256": "461c001aed557ffeb3997f64ef208297b985a4a9edfc1926b0c776ab73c1f69c",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "02c69f59e3832701f465fb692ea9b19bb8bbc7c752d2d623d2b3c8ceee2fff36.npz",
      "sha256": "2f6ac83050ad030d65fdd454516e870d6ee88386a23f358fdfb20646cfae894b",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 327680
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-8c7f139cfe1801ba1614bc353a8ec3101b4925791c39caed18924b8cf8a2a4e8",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.88671875,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 41,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 39,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 61,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58203125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第5轮

**当时目的与操作理由（原文）**

Targeted test of an empirically localized layer21 attention interaction component, removing only its projection from128 input-coordinate columns rather than ablating whole heads.

**本轮原记录的主分数**：`0.55859375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:1:counterfact_usual"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 319969,
  "id": "c-47da33c531b25b4be4ca066ead6afbeaf04b9885ba6726c020a9c5229b1d25fa",
  "l2": 1.1001122896400144,
  "parent": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "rationale": "Targeted test of an empirically localized layer21 attention interaction component, removing only its projection from128 input-coordinate columns rather than ablating whole heads.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 319969,
      "content_sha256": "fad4994918f190d09f05886230c40f39eb5afb6efb1730f5ae1d14437d88f2cf",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "ad97816fec9c1d2a53a09769a54ee72708a43e305f099b93f0d50fc0d0c2d818",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 319969
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-47da33c531b25b4be4ca066ead6afbeaf04b9885ba6726c020a9c5229b1d25fa",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.87890625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 45,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 42,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 58,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 32,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 44,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.55859375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第6轮

**当时目的与操作理由（原文）**

Predeclared half-dose of H2 to test strength dependence after unit-dose increased all8 focal margins but damaged17 counterfactual-usual answers.

**本轮原记录的主分数**：`0.578125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B1:T0:1:counterfact_usual"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 312194,
  "id": "c-5dd18666d85ca4145527324acd3d8702907b530f199debcf03779985d10bc88d",
  "l2": 0.5502893149968232,
  "parent": "c-47da33c531b25b4be4ca066ead6afbeaf04b9885ba6726c020a9c5229b1d25fa",
  "rationale": "Predeclared half-dose of H2 to test strength dependence after unit-dose increased all8 focal margins but damaged17 counterfactual-usual answers.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 312194,
      "content_sha256": "9b6a85553c8d01e56e3d24cb4fa6b81e3f99c0d035aae6e5d7c28b7c2abbe3a3",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "b21cfb5fbcc484215fbefda2d43d461d617c0dbdeb26cddf5f5c127de09ab4d7",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 312194
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-5dd18666d85ca4145527324acd3d8702907b530f199debcf03779985d10bc88d",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.8828125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 42,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 33,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.578125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第7轮

**当时目的与操作理由（原文）**

Round07: predeclared double-dose test of the layer21 attention interaction projection, following the observed half-dose and unit-dose tradeoff.

**本轮原记录的主分数**：`0.546875`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:1:counterfact_usual"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 323953,
  "id": "c-d63ab02f94402967e9f9c461869b2e73d6630815bbf570885b5c863482f1ca85",
  "l2": 2.199861485409231,
  "parent": "c-5dd18666d85ca4145527324acd3d8702907b530f199debcf03779985d10bc88d",
  "rationale": "Round07: predeclared double-dose test of the layer21 attention interaction projection, following the observed half-dose and unit-dose tradeoff.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 323953,
      "content_sha256": "4390588ef496cee3e08bc7271ea2e61b54e4a69fe2b0d42eabb13c7fbe3430bb",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "95df975c334ea0a51de690549e573513f87ca98268883422d85899fc75b3ad28",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 323953
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-d63ab02f94402967e9f9c461869b2e73d6630815bbf570885b5c863482f1ca85",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.876171875,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 41,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 45,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 58,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 28,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 42,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.734375,
    "repair_score": 0.546875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第8轮

**当时目的与操作理由（原文）**

Round08: opposite-sign control for the layer21 rank-one component after dose-dependent visual-margin gains and usual-task damage.

**本轮原记录的主分数**：`0.6015625`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-96c7f83f2ec18a79cb3d64d30dfdf2cf025ebe0e05b14b50742fa29738071561",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.6015625
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 319959,
  "id": "c-96c7f83f2ec18a79cb3d64d30dfdf2cf025ebe0e05b14b50742fa29738071561",
  "l2": 1.1001184256601122,
  "parent": "c-d63ab02f94402967e9f9c461869b2e73d6630815bbf570885b5c863482f1ca85",
  "rationale": "Round08: opposite-sign control for the layer21 rank-one component after dose-dependent visual-margin gains and usual-task damage.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 319959,
      "content_sha256": "ee001065f3c77c80a50630cda2e3b92eac58fa649c1505888887eafc97e45edd",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "52a5a1834998942f75b417128f3df9d8de473813adfdbcd2fb73864e03ab8800",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 319959
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-96c7f83f2ec18a79cb3d64d30dfdf2cf025ebe0e05b14b50742fa29738071561",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.88984375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 59,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 44,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 41,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 61,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 56,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.765625,
    "repair_score": 0.6015625,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第9轮

**当时目的与操作理由（原文）**

Round09: test output-direction specificity while preserving the targeted edit's input coefficients, column set, rank and effective weight norm.

**本轮原记录的主分数**：`0.58203125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 318635,
  "id": "c-2b2241a0351e2652595374fbdf70aff9d13deeda2c3cb3c478296bc15d539a22",
  "l2": 1.1001122370154834,
  "parent": "c-96c7f83f2ec18a79cb3d64d30dfdf2cf025ebe0e05b14b50742fa29738071561",
  "rationale": "Round09: test output-direction specificity while preserving the targeted edit's input coefficients, column set, rank and effective weight norm.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 318635,
      "content_sha256": "e8c2cb76db08a69e1e6613fafe93f1042bf5c4d7a7aa686923949f300dbe45aa",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "abeb4ffc558fec4041f66fb582f71df12d3337c4c11d082c2170308a4b284126",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 318635
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-2b2241a0351e2652595374fbdf70aff9d13deeda2c3cb3c478296bc15d539a22",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.88515625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 42,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58203125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第10轮

**当时目的与操作理由（原文）**

Round10: norm-matched random-column control for the layer21 directional edit.

**本轮原记录的主分数**：`0.5859375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 305568,
  "id": "c-1eb8a499468ca6a937e8d951e2e4a92a5e63c1a6ac56a369d5e9cf4cbd6fb2ab",
  "l2": 1.1001126117661835,
  "parent": "c-2b2241a0351e2652595374fbdf70aff9d13deeda2c3cb3c478296bc15d539a22",
  "rationale": "Round10: norm-matched random-column control for the layer21 directional edit.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 305568,
      "content_sha256": "e1c768a6d1c2cfa63f7ebb52673fad7e968f48917801650f67dee51fc2d3acff",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "6ebd5d01d597fdbadc869e04cc39343d9aeb8e2a0eaee7dce269e8d2319b716a",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 305568
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-1eb8a499468ca6a937e8d951e2e4a92a5e63c1a6ac56a369d5e9cf4cbd6fb2ab",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.88515625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 61,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.5859375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第11轮

**当时目的与操作理由（原文）**

Round11: test early wording dependence using a direction estimated from original-image contrasts with both answers correct, rather than a late failure-associated decision component.

**本轮原记录的主分数**：`0.578125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 314716,
  "id": "c-50b63a80a75c143aea8b5b448e00da6645b08247e1e1e5e4249ddfcfcdbf177f",
  "l2": 0.8485383418420133,
  "parent": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "rationale": "Round11: test early wording dependence using a direction estimated from original-image contrasts with both answers correct, rather than a late failure-associated decision component.",
  "tensors": {
    "model.language_model.layers.3.self_attn.o_proj.weight": {
      "base_sha256": "78ba4f49538bc809b3afdcb5b1b770849ed01ec088219e38f500306639a8eb75",
      "changed": 314716,
      "content_sha256": "ec7055e2482d528d39e85fe167d71cf5d2112a809512b9a027f72710caa6b658",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ccdab77ef5cea5b6f775cc8bf8eba6fedbb1579520794fa8ef30a026c5719d3c.npz",
      "sha256": "425e41ef414730cba2da609c6756a5b84949bf13dd67b5d3961bbd14892c4bb6",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 314716
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-50b63a80a75c143aea8b5b448e00da6645b08247e1e1e5e4249ddfcfcdbf177f",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.88515625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 37,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.578125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第12轮

**当时目的与操作理由（原文）**

Round12: prespecified double-dose test of the early wording component after unit dose changed the intended residual projection but failed the focal-margin prediction.

**本轮原记录的主分数**：`0.58984375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 320850,
  "id": "c-a65f9fb93eaecf755bcf7107ddfb0a6b278ffa2d1ca62d771106709fb0cd2f58",
  "l2": 1.6966307623764962,
  "parent": "c-50b63a80a75c143aea8b5b448e00da6645b08247e1e1e5e4249ddfcfcdbf177f",
  "rationale": "Round12: prespecified double-dose test of the early wording component after unit dose changed the intended residual projection but failed the focal-margin prediction.",
  "tensors": {
    "model.language_model.layers.3.self_attn.o_proj.weight": {
      "base_sha256": "78ba4f49538bc809b3afdcb5b1b770849ed01ec088219e38f500306639a8eb75",
      "changed": 320850,
      "content_sha256": "ffe752a5baf8b8ea2a9d3857ad360a38bcaf5b611c9813039bbe75693dd482c9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ccdab77ef5cea5b6f775cc8bf8eba6fedbb1579520794fa8ef30a026c5719d3c.npz",
      "sha256": "cf1e0496f7ae2c50172176a35f123f66d4c0b1469e0432df6b3d6d063ee2d990",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 320850
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-a65f9fb93eaecf755bcf7107ddfb0a6b278ffa2d1ca62d771106709fb0cd2f58",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.8875,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 41,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 37,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58984375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第13轮

**当时目的与操作理由（原文）**

Round13: predeclared opposite-sign control for the early wording edit after both removal strengths failed to improve the mean focal T1 margin over W0.

**本轮原记录的主分数**：`0.5859375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 314712,
  "id": "c-92353818af49361c066343c06696cc111c1b62435851de6ebf5eb46f584f8ea8",
  "l2": 0.8485574974718633,
  "parent": "c-a65f9fb93eaecf755bcf7107ddfb0a6b278ffa2d1ca62d771106709fb0cd2f58",
  "rationale": "Round13: predeclared opposite-sign control for the early wording edit after both removal strengths failed to improve the mean focal T1 margin over W0.",
  "tensors": {
    "model.language_model.layers.3.self_attn.o_proj.weight": {
      "base_sha256": "78ba4f49538bc809b3afdcb5b1b770849ed01ec088219e38f500306639a8eb75",
      "changed": 314712,
      "content_sha256": "f55b3bc4b6efb0e036a3324c1ffa30d27ffbdaf31bc503eab823ee6ef1056c0a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ccdab77ef5cea5b6f775cc8bf8eba6fedbb1579520794fa8ef30a026c5719d3c.npz",
      "sha256": "7bf8e60645aaf5044d91467a501cf647f97725fefd1f7b3a1c3524fdc96bc22e",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 314712
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-92353818af49361c066343c06696cc111c1b62435851de6ebf5eb46f584f8ea8",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.8859375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 41,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.5859375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第14轮

**当时目的与操作理由（原文）**

Round14: test whether removing two usual-task mean components from the layer21 input coefficients reduces the visual/usual tradeoff at matched ideal weight norm.

**本轮原记录的主分数**：`0.5859375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 310409,
  "id": "c-5104c445e9c09230c1db823f22144c0f22e0ed43cc0751a127b5e249e0ffe2d5",
  "l2": 1.1001180463550413,
  "parent": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "rationale": "Round14: test whether removing two usual-task mean components from the layer21 input coefficients reduces the visual/usual tradeoff at matched ideal weight norm.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 310409,
      "content_sha256": "4bc6410182f2e4d4b6a735180b329d2e7ca1070bd487b18b47a1a0a93632250f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "cf2698a6a1af22c594cb9bc567386c73023b632fb011a8de3d9e02a190b2742a",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 310409
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-5104c445e9c09230c1db823f22144c0f22e0ed43cc0751a127b5e249e0ffe2d5",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.8859375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.5859375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第15轮

**当时目的与操作理由（原文）**

Round15: predeclared double-dose test of the layer21 control-mean-null coefficient edit, retaining the original direction and columns without refitting to replication results.

**本轮原记录的主分数**：`0.5859375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 317890,
  "id": "c-60058b638402c047f4f437263d333d8d6a856ad1dee2ccfa9ccbf285d88f203d",
  "l2": 2.1998785244064893,
  "parent": "c-5104c445e9c09230c1db823f22144c0f22e0ed43cc0751a127b5e249e0ffe2d5",
  "rationale": "Round15: predeclared double-dose test of the layer21 control-mean-null coefficient edit, retaining the original direction and columns without refitting to replication results.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 317890,
      "content_sha256": "baf64dd9f26f0355af9c2be58ba81c3bb68b69a0c9a855031184e151447fff80",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "4a7d8d062ff45a4c9c558eeb40bf1f89d96d82426d2cc4edc37a14b73c258968",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 317890
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-60058b638402c047f4f437263d333d8d6a856ad1dee2ccfa9ccbf285d88f203d",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.88515625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 37,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 61,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 50,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.5859375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第16轮

**当时目的与操作理由（原文）**

Round16: predeclared opposite-sign control for the layer21 control-mean-null edit after two removal doses showed construction-panel benefits but failed the positive replication prediction.

**本轮原记录的主分数**：`0.5859375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 310411,
  "id": "c-9eb101e364b5298f5b0c928f7ec7123bd275284d3e90b5168775ddbc3de09013",
  "l2": 1.1000526969619033,
  "parent": "c-60058b638402c047f4f437263d333d8d6a856ad1dee2ccfa9ccbf285d88f203d",
  "rationale": "Round16: predeclared opposite-sign control for the layer21 control-mean-null edit after two removal doses showed construction-panel benefits but failed the positive replication prediction.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 310411,
      "content_sha256": "235aff1c93403ca0ec3a44d4971c854b4a1d00b45144af182b599b849f956dfc",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "8d439f69a0bb725b77250722bd0954b1a98980ff56f112ab6127f7c62319c7f0",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 310411
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-9eb101e364b5298f5b0c928f7ec7123bd275284d3e90b5168775ddbc3de09013",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.886328125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 42,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 42,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.5859375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第17轮

**当时目的与操作理由（原文）**

Round17: output-direction control for H4, reusing round09's fixed orthogonal direction while preserving H4's columns and projected coefficients.

**本轮原记录的主分数**：`0.58203125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 309446,
  "id": "c-ed4169011dcf38aa1c3a4933d92ee7418c8362a79e5ef0f5cd09b69fc48f009f",
  "l2": 1.1001180344182098,
  "parent": "c-9eb101e364b5298f5b0c928f7ec7123bd275284d3e90b5168775ddbc3de09013",
  "rationale": "Round17: output-direction control for H4, reusing round09's fixed orthogonal direction while preserving H4's columns and projected coefficients.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 309446,
      "content_sha256": "9aeb42ab716a118b5bcdc1839b421233da003114f6572ee570e08e5d7d0fa27b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "4ee2cf82f08d5cde230690d3adfa2384bffbef1cbe0536f4184c00dc7f6a61db",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 309446
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-ed4169011dcf38aa1c3a4933d92ee7418c8362a79e5ef0f5cd09b69fc48f009f",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.885546875,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58203125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第18轮

**当时目的与操作理由（原文）**

Round18: test the causal contribution of selected layer21 MLP writes into the shared decision direction, separately from the attention projection.

**本轮原记录的主分数**：`0.57421875`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:1:counterfact_usual"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 312333,
  "id": "c-e5a70aaf8c745ff627c39102070d8e927d480cb63d1703296202f063015613ef",
  "l2": 0.7422913632188067,
  "parent": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "rationale": "Round18: test the causal contribution of selected layer21 MLP writes into the shared decision direction, separately from the attention projection.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 312333,
      "content_sha256": "43c46e86aa60716b0c2eaf9504297d32d214a55debe64ef5c1882900b133c1ac",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "ef9a8b7b38a5b0c8e6662b4e69f2036d7ab1b77223a22af5ee8108f340a8fb93",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 312333
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-e5a70aaf8c745ff627c39102070d8e927d480cb63d1703296202f063015613ef",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.882421875,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 45,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 42,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 58,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 32,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 45,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.57421875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第19轮

**当时目的与操作理由（原文）**

Round19: predeclared double-dose test of the selected layer21 MLP writes into the shared decision direction, retaining round18's direction, coefficients, columns, and measurement panel.

**本轮原记录的主分数**：`0.578125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:1:counterfact_usual"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 320075,
  "id": "c-6fc12077d830a7e8498fb264c9e42c3e41bc12976001b9a5d247692b23abcd37",
  "l2": 1.4842613790446755,
  "parent": "c-e5a70aaf8c745ff627c39102070d8e927d480cb63d1703296202f063015613ef",
  "rationale": "Round19: predeclared double-dose test of the selected layer21 MLP writes into the shared decision direction, retaining round18's direction, coefficients, columns, and measurement panel.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 320075,
      "content_sha256": "39e8edbd72c4bfb0cb42415effbe6f7b28cd6336626a0e2bb681ab3d018ada8f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "bf88655d8ff979eecfeddfcb7c1635e02d2fdd3195aa2f45fc815e3ab27eff64",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 320075
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-6fc12077d830a7e8498fb264c9e42c3e41bc12976001b9a5d247692b23abcd37",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.8828125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 44,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 44,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 42,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 59,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 31,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 49,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 54,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.734375,
    "repair_score": 0.578125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第20轮

**当时目的与操作理由（原文）**

Round20: predeclared opposite-sign unit control for the layer21 MLP component after unit and double removal showed stronger visual margins alongside stronger usual-task costs.

**本轮原记录的主分数**：`0.58984375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 312319,
  "id": "c-ebc8b9866a167afb804d78c59e5a047ccc43ec65b93ec49e262f2c0d3e8822b6",
  "l2": 0.7423094273787875,
  "parent": "c-6fc12077d830a7e8498fb264c9e42c3e41bc12976001b9a5d247692b23abcd37",
  "rationale": "Round20: predeclared opposite-sign unit control for the layer21 MLP component after unit and double removal showed stronger visual margins alongside stronger usual-task costs.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 312319,
      "content_sha256": "91c79558baf3cfe62b2ed18384a3f3ae8363ed71c1193f5da9dd57470606ae5c",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "49b913cda41b7d6ca68a1fb701bd0d79a0ab25ada0ff4fa800f073992b5fe5f0",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 312319
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-ebc8b9866a167afb804d78c59e5a047ccc43ec65b93ec49e262f2c0d3e8822b6",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.888671875,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 39,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 59,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 44,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 39,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 61,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 56,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58984375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第21轮

**当时目的与操作理由（原文）**

Round21: predeclared orthogonal output-direction control for the layer21 MLP component, preserving its selected columns and input coefficients while matching round18's effective BF16 edit norm.

**本轮原记录的主分数**：`0.58203125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 311487,
  "id": "c-d286ecdf8fe05fad98dfc4fc6433a088455edc6a0408fcc2406cd056c1c65dbe",
  "l2": 0.7422915380205528,
  "parent": "c-ebc8b9866a167afb804d78c59e5a047ccc43ec65b93ec49e262f2c0d3e8822b6",
  "rationale": "Round21: predeclared orthogonal output-direction control for the layer21 MLP component, preserving its selected columns and input coefficients while matching round18's effective BF16 edit norm.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 311487,
      "content_sha256": "d829e647bd6b57ac5936b533b37c0832dab2fa81142d1314cb416c4297d29c3d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "c703c11c27aed07573f36127cce00e5e1b566e6a758b41b037d6decef9e43160",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 311487
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-d286ecdf8fe05fad98dfc4fc6433a088455edc6a0408fcc2406cd056c1c65dbe",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.8859375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58203125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第22轮

**当时目的与操作理由（原文）**

Round22: predeclared half-amplification of the original H2 attention component, without an MLP edit or refitting.

**本轮原记录的主分数**：`0.5859375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 312190,
  "id": "c-df5bc2da4bb2092a354e13a46792600583e2d04bf4bd65d2e94cf5595173eb84",
  "l2": 0.5502904865171648,
  "parent": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "rationale": "Round22: predeclared half-amplification of the original H2 attention component, without an MLP edit or refitting.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 312190,
      "content_sha256": "e66a6e4fc6dd40da5f0e2534b4b85ff5e36e26312d8671d79335ac62749d36f9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "b8ad6db06c8893e7c11d13b5dff18d8e584e040198ba58289be42fb9a09fe818",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 312190
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-df5bc2da4bb2092a354e13a46792600583e2d04bf4bd65d2e94cf5595173eb84",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.88828125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 59,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 39,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 61,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 56,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.5859375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第23轮

**当时目的与操作理由（原文）**

Round23: predeclared double-amplification test of the original H2 attention component, retaining its direction, columns, coefficients, and measurement panel.

**本轮原记录的主分数**：`0.609375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-9652d71dc3f8671029f03a284ca51fb4e013a51510c29e99d4fe3ae3424dd53d",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.609375
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 323956,
  "id": "c-9652d71dc3f8671029f03a284ca51fb4e013a51510c29e99d4fe3ae3424dd53d",
  "l2": 2.199869051554772,
  "parent": "c-df5bc2da4bb2092a354e13a46792600583e2d04bf4bd65d2e94cf5595173eb84",
  "rationale": "Round23: predeclared double-amplification test of the original H2 attention component, retaining its direction, columns, coefficients, and measurement panel.",
  "tensors": {
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 323956,
      "content_sha256": "3c5b234204d0ecdb6a40cfb58d4419b592553da741d64e2899af54c0f6b1183a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "c5690b24080a552cd0bd440c242faa0e4041fbc12283fafb5a1c58d3a8f00730",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 323956
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-9652d71dc3f8671029f03a284ca51fb4e013a51510c29e99d4fe3ae3424dd53d",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.8921875,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 39,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 59,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 45,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 54,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 56,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 42,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 56,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 53,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.78125,
    "repair_score": 0.609375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第24轮

**当时目的与操作理由（原文）**

Round24: test the fixed H6 mean-null layer21 MLP component, isolating it from all attention edits.

**本轮原记录的主分数**：`0.58984375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 306792,
  "id": "c-76de5f8396ab03a50e8daefbd2d1831abe7884b907f710253a97fa41b98dcf1a",
  "l2": 0.7422826244889801,
  "parent": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "rationale": "Round24: test the fixed H6 mean-null layer21 MLP component, isolating it from all attention edits.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 306792,
      "content_sha256": "6830dba53a1f18d351339c2b5202476e30ac40a4153b5adeb210f5fa050a07e6",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "177e3bff6c89db8290b0142248d29eef344828daeff6796d0c633e1ae5a7e284",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 306792
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-76de5f8396ab03a50e8daefbd2d1831abe7884b907f710253a97fa41b98dcf1a",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.886328125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58984375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第25轮

**当时目的与操作理由（原文）**

Round25: predeclared opposite-sign unit control for the fixed H6 mean-null MLP component.

**本轮原记录的主分数**：`0.58203125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 306772,
  "id": "c-fe7105f305005bda16c91d20f8196fb618d22b68da6593e3c1bc9dd7a44b7cdb",
  "l2": 0.742280321369501,
  "parent": "c-76de5f8396ab03a50e8daefbd2d1831abe7884b907f710253a97fa41b98dcf1a",
  "rationale": "Round25: predeclared opposite-sign unit control for the fixed H6 mean-null MLP component.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 306772,
      "content_sha256": "5d8f8a59f4346b84cb9e3144267c00d1bd3997b6144acb890a93cf137949d09d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "cf3a7c61025dd915e27f98dffb3d814de6c06b65c0d89d9eed740eaaa9dde367",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 306772
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-fe7105f305005bda16c91d20f8196fb618d22b68da6593e3c1bc9dd7a44b7cdb",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.8859375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58203125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第26轮

**当时目的与操作理由（原文）**

Round26: predeclared orthogonal-output control for the fixed H6 mean-null MLP component, matching round24's effective BF16 edit norm without outcome-based calibration.

**本轮原记录的主分数**：`0.58203125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 306354,
  "id": "c-be1b686068c83a165056441926e73ba8b8b22ac9fb48c14768e29168f3a55577",
  "l2": 0.7422827000873106,
  "parent": "c-fe7105f305005bda16c91d20f8196fb618d22b68da6593e3c1bc9dd7a44b7cdb",
  "rationale": "Round26: predeclared orthogonal-output control for the fixed H6 mean-null MLP component, matching round24's effective BF16 edit norm without outcome-based calibration.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 306354,
      "content_sha256": "90b8640b0f63496d5962a8318c7459ac42c8aec5a86c5ed510458d9b1562390a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "58ebc41b3ba18c2a56d67f5672da757150bf036856b70383d43b34a195605e05",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 306354
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-be1b686068c83a165056441926e73ba8b8b22ac9fb48c14768e29168f3a55577",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.88515625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58203125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第27轮

**当时目的与操作理由（原文）**

Round27 of 30: first cell of the predeclared H7 sign factorial, amplifying the original layer21 attention and MLP components together without refitting.

**本轮原记录的主分数**：`0.6015625`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 632278,
  "id": "c-7877560048b35f59d200b51466fc47a58354196c6297ffdfede2879d61b713f6",
  "l2": 1.3271336920040524,
  "parent": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "rationale": "Round27 of 30: first cell of the predeclared H7 sign factorial, amplifying the original layer21 attention and MLP components together without refitting.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 312319,
      "content_sha256": "91c79558baf3cfe62b2ed18384a3f3ae8363ed71c1193f5da9dd57470606ae5c",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "49b913cda41b7d6ca68a1fb701bd0d79a0ab25ada0ff4fa800f073992b5fe5f0",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 312319
    },
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 319959,
      "content_sha256": "ee001065f3c77c80a50630cda2e3b92eac58fa649c1505888887eafc97e45edd",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "52a5a1834998942f75b417128f3df9d8de473813adfdbcd2fb73864e03ab8800",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 319959
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-7877560048b35f59d200b51466fc47a58354196c6297ffdfede2879d61b713f6",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.891015625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 38,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 59,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 45,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 54,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 56,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 42,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 56,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 53,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.78125,
    "repair_score": 0.6015625,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第28轮

**当时目的与操作理由（原文）**

Round28 of 30: predeclared H7 opposed-sign cell, attention amplification and MLP removal, using unchanged original components and absolute-W0 weights.

**本轮原记录的主分数**：`0.59375`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 632292,
  "id": "c-623fabb1714010e428d15afe552c9315a18e258ccb9bc14ca82d48085ce2997a",
  "l2": 1.3271235882110295,
  "parent": "c-7877560048b35f59d200b51466fc47a58354196c6297ffdfede2879d61b713f6",
  "rationale": "Round28 of 30: predeclared H7 opposed-sign cell, attention amplification and MLP removal, using unchanged original components and absolute-W0 weights.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 312333,
      "content_sha256": "43c46e86aa60716b0c2eaf9504297d32d214a55debe64ef5c1882900b133c1ac",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "ef9a8b7b38a5b0c8e6662b4e69f2036d7ab1b77223a22af5ee8108f340a8fb93",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 312333
    },
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 319959,
      "content_sha256": "ee001065f3c77c80a50630cda2e3b92eac58fa649c1505888887eafc97e45edd",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "52a5a1834998942f75b417128f3df9d8de473813adfdbcd2fb73864e03ab8800",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 319959
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-623fabb1714010e428d15afe552c9315a18e258ccb9bc14ca82d48085ce2997a",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.8890625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 58,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 38,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.59375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第29轮

**当时目的与操作理由（原文）**

Round29 of 30: predeclared H7 reverse opposed-sign cell, attention removal and MLP amplification, with fixed original components and absolute-W0 weights.

**本轮原记录的主分数**：`0.58203125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 632288,
  "id": "c-328b6ed7faf0ca02f547dad547680e82d7bce1dbcb6a47ed83cee89eb4499b7f",
  "l2": 1.327128605596465,
  "parent": "c-623fabb1714010e428d15afe552c9315a18e258ccb9bc14ca82d48085ce2997a",
  "rationale": "Round29 of 30: predeclared H7 reverse opposed-sign cell, attention removal and MLP amplification, with fixed original components and absolute-W0 weights.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 312319,
      "content_sha256": "91c79558baf3cfe62b2ed18384a3f3ae8363ed71c1193f5da9dd57470606ae5c",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "49b913cda41b7d6ca68a1fb701bd0d79a0ab25ada0ff4fa800f073992b5fe5f0",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 312319
    },
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 319969,
      "content_sha256": "fad4994918f190d09f05886230c40f39eb5afb6efb1730f5ae1d14437d88f2cf",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "ad97816fec9c1d2a53a09769a54ee72708a43e305f099b93f0d50fc0d0c2d818",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 319969
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-328b6ed7faf0ca02f547dad547680e82d7bce1dbcb6a47ed83cee89eb4499b7f",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.883984375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 60,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 40,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 57,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 36,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 61,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 61,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.75,
    "repair_score": 0.58203125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第30轮

**当时目的与操作理由（原文）**

Round30 of 30, final authorized candidate: predeclared H7 both-removed cell using the original layer21 attention and MLP components, without refitting.

**本轮原记录的主分数**：`0.5703125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:1:counterfact_usual"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 632302,
  "id": "c-3028debe65ac5977e092d2f76f7a2fcc00f304dd5e5925ba5de6f94bad45268f",
  "l2": 1.3271185017647178,
  "parent": "c-328b6ed7faf0ca02f547dad547680e82d7bce1dbcb6a47ed83cee89eb4499b7f",
  "rationale": "Round30 of 30, final authorized candidate: predeclared H7 both-removed cell using the original layer21 attention and MLP components, without refitting.",
  "tensors": {
    "model.language_model.layers.21.mlp.down_proj.weight": {
      "base_sha256": "bdd9248b5ebba0957315489d50847334cfaa9b7092c986e7bf0255af16dc2f9c",
      "changed": 312333,
      "content_sha256": "43c46e86aa60716b0c2eaf9504297d32d214a55debe64ef5c1882900b133c1ac",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d6014053f46dec0ae91ed7d235611fe74ad62c5b9adebca1e3b7aeabaf29832.npz",
      "sha256": "ef9a8b7b38a5b0c8e6662b4e69f2036d7ab1b77223a22af5ee8108f340a8fb93",
      "shape": [
        2560,
        9728
      ],
      "stored_coordinates": 312333
    },
    "model.language_model.layers.21.self_attn.o_proj.weight": {
      "base_sha256": "b95112586e629ffefa21338a20bb5c1dc7f09be1d9575b413e5c731b00a7a800",
      "changed": 319969,
      "content_sha256": "fad4994918f190d09f05886230c40f39eb5afb6efb1730f5ae1d14437d88f2cf",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "abae8c26dc6453d0232681e7da2b9ab77c9f791c180616e7e0c827113990a1ab.npz",
      "sha256": "ad97816fec9c1d2a53a09769a54ee72708a43e305f099b93f0d50fc0d0c2d818",
      "shape": [
        2560,
        4096
      ],
      "stored_coordinates": 319969
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-3028debe65ac5977e092d2f76f7a2fcc00f304dd5e5925ba5de6f94bad45268f",
  "full_development": true,
  "protocol": "19bd385548e9abb64cc4d9173f27f93378e25c517606c6aeb6eeed98a445afcd",
  "summary": {
    "accuracy": 0.880078125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 52,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:counterfact_usual": {
        "correct": 44,
        "n": 64
      },
      "B0:T0:1:counterfact_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T0:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 43,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 41,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 45,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B1:T0:0:counterfact_visual": {
        "correct": 58,
        "n": 64
      },
      "B1:T0:0:no_image_usual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:0:original_usual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:1:counterfact_usual": {
        "correct": 30,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 63,
        "n": 64
      },
      "B1:T0:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B1:T0:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:0:counterfact_usual": {
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B1:T1:0:no_image_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T1:1:counterfact_usual": {
        "correct": 43,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 54,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 51,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B1:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      }
    },
    "format_errors": 0,
    "n": 2560,
    "primary_groups": 64,
    "primary_joint": 0.734375,
    "repair_score": 0.5703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

