# Qwen-v8-C：逐轮目的、修改与结果

本页逐轮转录已归档值，不重新评分、不运行模型。共50个完整候选；不是新增50次实验。研究者当时的理由按原文保留，其中预期不能读作已验证结果。每轮均从其记录指定的基线和父候选解释，不能默认累加补丁。

原始完整档案（含逐题答案）：

- [experiments/wsp-vlm-open-repair-v8x50-2026-11-05/closeout-evidence.json.gz](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8x50-2026-11-05/closeout-evidence.json.gz)

## 第1轮

**当时目的与操作理由（原文）**

Round 1 hypothesis: improve visual-scope routing for T1 by moving token 41566 (pictured) halfway toward norm-matched token 2168 (image), then preserving the original pictured-row norm. One tied embedding/output row; no gold-answer vectors, gradient training, or prompt changes. Hypothesis selected from complete development successes and failures.

**本轮原记录的主分数**：`0.6328125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-92fb2d79502294f62617c0a32f9d0a4237cbaa06e3506a594c0c9d90a2ca2774",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.6328125
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 2553,
  "id": "c-92fb2d79502294f62617c0a32f9d0a4237cbaa06e3506a594c0c9d90a2ca2774",
  "l2": 0.82134025383556,
  "parent": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "rationale": "Round 1 hypothesis: improve visual-scope routing for T1 by moving token 41566 (pictured) halfway toward norm-matched token 2168 (image), then preserving the original pictured-row norm. One tied embedding/output row; no gold-answer vectors, gradient training, or prompt changes. Hypothesis selected from complete development successes and failures.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 2553,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "64440688bb5825e7c824604659d27027ee1f1b67ef7877c576a66588aaea28dd",
      "shape": [
        151936,
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-92fb2d79502294f62617c0a32f9d0a4237cbaa06e3506a594c0c9d90a2ca2774",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.891796875,
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
        "correct": 51,
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
        "correct": 49,
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
    "repair_score": 0.6328125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第2轮

**当时目的与操作理由（原文）**

Round 2: replace pictured embedding with the W0 image direction at pictured's original norm. Tests full semantic substitution versus round 1's half interpolation. Only the same tied row is changed relative to W0; no answer-label fitting.

**本轮原记录的主分数**：`0.609375`；保留原始0–1尺度。

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
  "changed_scalars": 2558,
  "id": "c-6d7debee48d552e5eacf478b470960bdb9df5572c20f6eb637a442fec4e79c15",
  "l2": 1.537451783426716,
  "parent": "c-92fb2d79502294f62617c0a32f9d0a4237cbaa06e3506a594c0c9d90a2ca2774",
  "rationale": "Round 2: replace pictured embedding with the W0 image direction at pictured's original norm. Tests full semantic substitution versus round 1's half interpolation. Only the same tied row is changed relative to W0; no answer-label fitting.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 2558,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "2af5a743dbae69581b7f8cd4eefef771d0caa98e19f05cbef92bb85af3fe8117",
      "shape": [
        151936,
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-6d7debee48d552e5eacf478b470960bdb9df5572c20f6eb637a442fec4e79c15",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
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
        "correct": 46,
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
        "correct": 48,
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
    "repair_score": 0.609375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第3轮

**当时目的与操作理由（原文）**

Round 3: restore pictured to round 1's norm-preserving half-image mixture and independently move bigger halfway toward norm-matched larger. Tests comparator lexical semantics, not a stronger image substitution. Two tied embedding rows; parameters computed from W0 vectors, no label-vector fitting.

**本轮原记录的主分数**：`0.640625`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-15d83676f0f77710cf6952ee4a874bbc11f6806fef15398f06bb06aa75801089",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.640625
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 5106,
  "id": "c-15d83676f0f77710cf6952ee4a874bbc11f6806fef15398f06bb06aa75801089",
  "l2": 0.9486795644729441,
  "parent": "c-6d7debee48d552e5eacf478b470960bdb9df5572c20f6eb637a442fec4e79c15",
  "rationale": "Round 3: restore pictured to round 1's norm-preserving half-image mixture and independently move bigger halfway toward norm-matched larger. Tests comparator lexical semantics, not a stronger image substitution. Two tied embedding rows; parameters computed from W0 vectors, no label-vector fitting.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 5106,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "ad09a8630f910738746104596f2769b27d0d65da6f317de968152c8a0bd040c7",
      "shape": [
        151936,
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-15d83676f0f77710cf6952ee4a874bbc11f6806fef15398f06bb06aa75801089",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.89375,
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
        "correct": 51,
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
        "correct": 51,
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
        "correct": 50,
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
    "primary_joint": 0.75,
    "repair_score": 0.640625,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第4轮

**当时目的与操作理由（原文）**

Round 4: retain round 3's pictured/image and bigger/larger half mixtures, add a norm-preserving half mixture of normally toward typically. Tests usual-size lexical scope across T1 image and no-image conditions. No answer-specific edits or gradient fitting.

**本轮原记录的主分数**：`0.671875`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-f87cd0a3c923beda41209a1c260ff70e54397d34bcfdf898d1d19b2bc42924e6",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.671875
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 7657,
  "id": "c-f87cd0a3c923beda41209a1c260ff70e54397d34bcfdf898d1d19b2bc42924e6",
  "l2": 1.120963349830906,
  "parent": "c-15d83676f0f77710cf6952ee4a874bbc11f6806fef15398f06bb06aa75801089",
  "rationale": "Round 4: retain round 3's pictured/image and bigger/larger half mixtures, add a norm-preserving half mixture of normally toward typically. Tests usual-size lexical scope across T1 image and no-image conditions. No answer-specific edits or gradient fitting.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 7657,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "b429326d883d2fabcea727371d3bf8f7e04771929d225fa3e304aabe6a03904d",
      "shape": [
        151936,
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f87cd0a3c923beda41209a1c260ff70e54397d34bcfdf898d1d19b2bc42924e6",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.89765625,
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
        "correct": 51,
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
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 54,
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
    "primary_joint": 0.75,
    "repair_score": 0.671875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第5轮

**当时目的与操作理由（原文）**

Round 5: add norm-preserving half interpolation of hyphenated -world token 30084 toward standalone world token 1879, retaining round 4. Tests whether real-world tokenization weakens usual-scope interpretation; protected original-usual T1O1 already has a two-answer loss and must not lose another.

**本轮原记录的主分数**：`0.67578125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-a352868699b557b40e36527fd5f05db47c569af794deeab85bee37271049adc8",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.67578125
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 10206,
  "id": "c-a352868699b557b40e36527fd5f05db47c569af794deeab85bee37271049adc8",
  "l2": 1.2058780794020594,
  "parent": "c-f87cd0a3c923beda41209a1c260ff70e54397d34bcfdf898d1d19b2bc42924e6",
  "rationale": "Round 5: add norm-preserving half interpolation of hyphenated -world token 30084 toward standalone world token 1879, retaining round 4. Tests whether real-world tokenization weakens usual-scope interpretation; protected original-usual T1O1 already has a two-answer loss and must not lose another.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-a352868699b557b40e36527fd5f05db47c569af794deeab85bee37271049adc8",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.898828125,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 53,
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
    "primary_joint": 0.75,
    "repair_score": 0.67578125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第6轮

**当时目的与操作理由（原文）**

Round 6: retain round 5 and move sizes token 12282 halfway toward norm-matched size token 1379, preserving sizes' W0 norm. Tests whether the plural size representation contributes to remaining T1 visual failures. Full protected-cell evaluation required.

**本轮原记录的主分数**：`0.67578125`；保留原始0–1尺度。

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
  "changed_scalars": 12747,
  "id": "c-290e6b16d704f30377bd688016a16dcc8dcd01d6f6d757e8b9457ea31321b283",
  "l2": 1.2818227945251928,
  "parent": "c-a352868699b557b40e36527fd5f05db47c569af794deeab85bee37271049adc8",
  "rationale": "Round 6: retain round 5 and move sizes token 12282 halfway toward norm-matched size token 1379, preserving sizes' W0 norm. Tests whether the plural size representation contributes to remaining T1 visual failures. Full protected-cell evaluation required.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 12747,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4ef1b8dc19fb316c49ef00fb0ada2afcfac7a2a5e2e02b6eba3c274400a957c8",
      "shape": [
        151936,
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-290e6b16d704f30377bd688016a16dcc8dcd01d6f6d757e8b9457ea31321b283",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.899609375,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 55,
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
    "primary_joint": 0.75,
    "repair_score": 0.67578125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第7轮

**当时目的与操作理由（原文）**

Round 7: remove the sizes edit, retain round 5 lexical directions, and increase normally and typically embedding norms by 50% relative to those directions. Tests usual-scope signal amplitude across T0/T1 rather than synonym direction. Five changed embedding rows; tied output effects remain protected.

**本轮原记录的主分数**：`0.671875`；保留原始0–1尺度。

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
  "changed_scalars": 12769,
  "id": "c-9b761d77fc7fde7d5a3bf870402c340c90e3b807d64f4d74b53c4ee94d6e0eb4",
  "l2": 1.494639851531894,
  "parent": "c-290e6b16d704f30377bd688016a16dcc8dcd01d6f6d757e8b9457ea31321b283",
  "rationale": "Round 7: remove the sizes edit, retain round 5 lexical directions, and increase normally and typically embedding norms by 50% relative to those directions. Tests usual-scope signal amplitude across T0/T1 rather than synonym direction. Five changed embedding rows; tied output effects remain protected.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 12769,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "c0ac21ff8d726beb48c012f4d73bce954866bd544ebb1ed03e4d8978f8598441",
      "shape": [
        151936,
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-9b761d77fc7fde7d5a3bf870402c340c90e3b807d64f4d74b53c4ee94d6e0eb4",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.89765625,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 37,
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
        "correct": 50,
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
        "correct": 53,
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
    "primary_joint": 0.75,
    "repair_score": 0.671875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第8轮

**当时目的与操作理由（原文）**

Round 8: restore round 5 usual-scope rows; amplify pictured's half-image mixture and the W0 image embedding by 1.5. Tests visual-scope amplitude rather than semantic substitution or usual-scope amplitude. All five conditions and both arms remain protected.

**本轮原记录的主分数**：`0.67578125`；保留原始0–1尺度。

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
  "changed_scalars": 12771,
  "id": "c-adc6ed47dc42be8d9575a35e8df5f0e90d9e24467c495afdfd8924f6b895588e",
  "l2": 1.5397720384520817,
  "parent": "c-9b761d77fc7fde7d5a3bf870402c340c90e3b807d64f4d74b53c4ee94d6e0eb4",
  "rationale": "Round 8: restore round 5 usual-scope rows; amplify pictured's half-image mixture and the W0 image embedding by 1.5. Tests visual-scope amplitude rather than semantic substitution or usual-scope amplitude. All five conditions and both arms remain protected.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 12771,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "b849a7be5c979d9843e89a9dc894ff88674ba57ab6ee0cc6986784e59469658a",
      "shape": [
        151936,
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-adc6ed47dc42be8d9575a35e8df5f0e90d9e24467c495afdfd8924f6b895588e",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.897265625,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 54,
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
    "primary_joint": 0.75,
    "repair_score": 0.67578125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第9轮

**当时目的与操作理由（原文）**

Round 9: restore round 5 lexical embeddings and scale main visual merger LayerNorm gamma and beta by 0.85 from W0. Deep-stack merger norms remain W0. Tests attenuation of the normalized main visual stream, not a missing-neuron claim. No-image outputs should remain those of round 5.

**本轮原记录的主分数**：`0.6875`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-b1b18b47386351cf1baa391e40925473c7ff8c9042f9836fc0fe95b2737135e5",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.6875
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 12254,
  "id": "c-b1b18b47386351cf1baa391e40925473c7ff8c9042f9836fc0fe95b2737135e5",
  "l2": 6.685515274157851,
  "parent": "c-adc6ed47dc42be8d9575a35e8df5f0e90d9e24467c495afdfd8924f6b895588e",
  "rationale": "Round 9: restore round 5 lexical embeddings and scale main visual merger LayerNorm gamma and beta by 0.85 from W0. Deep-stack merger norms remain W0. Tests attenuation of the normalized main visual stream, not a missing-neuron claim. No-image outputs should remain those of round 5.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-b1b18b47386351cf1baa391e40925473c7ff8c9042f9836fc0fe95b2737135e5",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.9015625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 61,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 53,
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
        "correct": 39,
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
        "correct": 50,
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
        "correct": 53,
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
    "primary_joint": 0.765625,
    "repair_score": 0.6875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第10轮

**当时目的与操作理由（原文）**

Round 10: same round 5 lexical patch, but main visual merger normalization gamma/beta set to 1.15 times W0 instead of round 9's 0.85. Opposing hypothesis: stronger main visual features improve scope-conditioned judgments. All deep-stack norms are W0.

**本轮原记录的主分数**：`0.6640625`；保留原始0–1尺度。

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
  "changed_scalars": 12254,
  "id": "c-0ad8a431dec3c93fbbe5463f2902be5d8915d51cf337637f40c597b32633ce69",
  "l2": 6.682654147976846,
  "parent": "c-b1b18b47386351cf1baa391e40925473c7ff8c9042f9836fc0fe95b2737135e5",
  "rationale": "Round 10: same round 5 lexical patch, but main visual merger normalization gamma/beta set to 1.15 times W0 instead of round 9's 0.85. Opposing hypothesis: stronger main visual features improve scope-conditioned judgments. All deep-stack norms are W0.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "948f09043eb07cc5a0551d87f19f432fc238aaea2f6b0e053a42a97d23569d30",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "3ef857280b7e188f921c4f2e210ad012fbbaeee20f5e3797e67150a6bf60a6c2",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-0ad8a431dec3c93fbbe5463f2902be5d8915d51cf337637f40c597b32633ce69",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.896875,
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
        "correct": 62,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
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
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 35,
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
        "correct": 50,
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
        "correct": 55,
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
    "primary_joint": 0.75,
    "repair_score": 0.6640625,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第11轮

**当时目的与操作理由（原文）**

Round 11: round 5 lexical background; main merger restored to W0; only deepstack_merger_list.0 norm gamma/beta scaled to 0.85 of W0. Tests first deep-stack pathway attenuation independently of the successful main-merger attenuation.

**本轮原记录的主分数**：`0.6796875`；保留原始0–1尺度。

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
  "changed_scalars": 18398,
  "id": "c-4b2e1baa7956b30c339a2a190edb8546113f281559fee4eaaa7aacac3d61b2dd",
  "l2": 9.793465077872808,
  "parent": "c-0ad8a431dec3c93fbbe5463f2902be5d8915d51cf337637f40c597b32633ce69",
  "rationale": "Round 11: round 5 lexical background; main merger restored to W0; only deepstack_merger_list.0 norm gamma/beta scaled to 0.85 of W0. Tests first deep-stack pathway attenuation independently of the successful main-merger attenuation.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.visual.deepstack_merger_list.0.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "9be04788b1c0d5b8af8b3e6837d5a8169494428b54f79b5890b670fb280ae24b.npy",
      "sha256": "aa75f9ca01944f999f65bb6887c41c0dea5d3b2bd68dced31b6f451d71d57925",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "735e42aa2631d379dad19d13d8747529fc485859e7ed94620f7239ec9d12604b",
      "shape": [
        4096
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-4b2e1baa7956b30c339a2a190edb8546113f281559fee4eaaa7aacac3d61b2dd",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.898046875,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 61,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 54,
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
    "primary_joint": 0.75,
    "repair_score": 0.6796875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第12轮

**当时目的与操作理由（原文）**

Round 12: isolate deepstack_merger_list.0 normalization at 1.15 times W0, with other merger norms W0 and round 5 lexical background. Tests stronger first auxiliary visual-path features against round 11 attenuation.

**本轮原记录的主分数**：`0.6796875`；保留原始0–1尺度。

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
  "changed_scalars": 18398,
  "id": "c-2bec404a7aed9047a4758d5703b3edadacd088c9537370e5e0e5d13b9204694b",
  "l2": 9.804534227125435,
  "parent": "c-4b2e1baa7956b30c339a2a190edb8546113f281559fee4eaaa7aacac3d61b2dd",
  "rationale": "Round 12: isolate deepstack_merger_list.0 normalization at 1.15 times W0, with other merger norms W0 and round 5 lexical background. Tests stronger first auxiliary visual-path features against round 11 attenuation.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.visual.deepstack_merger_list.0.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "9be04788b1c0d5b8af8b3e6837d5a8169494428b54f79b5890b670fb280ae24b.npy",
      "sha256": "65fa059e4ae31d753808adb8e78f1d5a95e0ed170e038c30a83e2c73d5d86c90",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "882320ae46441c6812fd1e8dbce3c56d3a8ee44114d0d8e049774463fba36337",
      "shape": [
        4096
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-2bec404a7aed9047a4758d5703b3edadacd088c9537370e5e0e5d13b9204694b",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.899609375,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 54,
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
    "primary_joint": 0.75,
    "repair_score": 0.6796875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第13轮

**当时目的与操作理由（原文）**

Round 13: round 5 lexical background, only deepstack_merger_list.1 norm gamma/beta at 0.85 times W0. Restore main and other deep-stack norms to W0. Tests whether second auxiliary visual-path attenuation improves joint usual/visual reasoning.

**本轮原记录的主分数**：`0.67578125`；保留原始0–1尺度。

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
  "changed_scalars": 18398,
  "id": "c-1f289cb2891bd4bc8a605148256cc44880ae99700fc997301370cf31d217f457",
  "l2": 9.895636653109326,
  "parent": "c-2bec404a7aed9047a4758d5703b3edadacd088c9537370e5e0e5d13b9204694b",
  "rationale": "Round 13: round 5 lexical background, only deepstack_merger_list.1 norm gamma/beta at 0.85 times W0. Restore main and other deep-stack norms to W0. Tests whether second auxiliary visual-path attenuation improves joint usual/visual reasoning.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.visual.deepstack_merger_list.1.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "3e0efc4703a8e12dc9c849ce2a8293cc2d3fd4caf53c6920525d819416d02881.npy",
      "sha256": "d90fb62bfe712ae8e0b33fba9c18927ddae972ad2ee52a1cac602498552ca855",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.1.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "560c532031860531bd2f415a47e04cc88d7d4140097b4be709d2db61f8124e34.npy",
      "sha256": "b25f858790e1fa8d637b1ff57fff5632d6ad4550e2dc0bdcba4fd3d2d1fe6577",
      "shape": [
        4096
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-1f289cb2891bd4bc8a605148256cc44880ae99700fc997301370cf31d217f457",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.9,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 49,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 56,
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
    "primary_joint": 0.75,
    "repair_score": 0.67578125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第14轮

**当时目的与操作理由（原文）**

Round 14: only deepstack_merger_list.1 normalization gamma/beta at 1.15 times W0, other merger norms W0, fixed round 5 lexical patch. Tests second auxiliary-path amplification against round 13 attenuation.

**本轮原记录的主分数**：`0.67578125`；保留原始0–1尺度。

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
  "changed_scalars": 18398,
  "id": "c-51f566a67982237e855635ae3530cbe60b26020d118228a9c38a281e11a92e2c",
  "l2": 9.919671378472762,
  "parent": "c-1f289cb2891bd4bc8a605148256cc44880ae99700fc997301370cf31d217f457",
  "rationale": "Round 14: only deepstack_merger_list.1 normalization gamma/beta at 1.15 times W0, other merger norms W0, fixed round 5 lexical patch. Tests second auxiliary-path amplification against round 13 attenuation.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.visual.deepstack_merger_list.1.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "3e0efc4703a8e12dc9c849ce2a8293cc2d3fd4caf53c6920525d819416d02881.npy",
      "sha256": "aa1a1d80e08b41776f2a3112c59d13bec234df0b059eba6547ca6e9eb4e4db9b",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.1.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "560c532031860531bd2f415a47e04cc88d7d4140097b4be709d2db61f8124e34.npy",
      "sha256": "9ed7eb9dca4e4a498a3c15d937ef48742f4c7eb4802f097a95c60bcc6ef819e7",
      "shape": [
        4096
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-51f566a67982237e855635ae3530cbe60b26020d118228a9c38a281e11a92e2c",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.89921875,
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
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 55,
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
    "primary_joint": 0.75,
    "repair_score": 0.67578125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第15轮

**当时目的与操作理由（原文）**

Round 15: isolate deepstack_merger_list.2 normalization gamma/beta at 0.85 times W0, with other merger norms W0 and round 5 lexical background. Tests attenuation of the third auxiliary visual representation.

**本轮原记录的主分数**：`0.65625`；保留原始0–1尺度。

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
  "changed_scalars": 18398,
  "id": "c-a428b61111165b3f6628c0e0f482bb6d3497135ab9bb3516d26ffc6354c9708f",
  "l2": 9.830155963608913,
  "parent": "c-51f566a67982237e855635ae3530cbe60b26020d118228a9c38a281e11a92e2c",
  "rationale": "Round 15: isolate deepstack_merger_list.2 normalization gamma/beta at 0.85 times W0, with other merger norms W0 and round 5 lexical background. Tests attenuation of the third auxiliary visual representation.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "4ccf0c2047b9c45a441245f9c70a69dfb98521eadd0663a222626dae4b1ec0f4",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "b3663fca4ce2e840c14411396489708cd4e506e82ac70ad972d8286d525e7201",
      "shape": [
        4096
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-a428b61111165b3f6628c0e0f482bb6d3497135ab9bb3516d26ffc6354c9708f",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.8953125,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 49,
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
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
    "primary_joint": 0.75,
    "repair_score": 0.65625,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第16轮

**当时目的与操作理由（原文）**

Round 16: isolate deepstack_merger_list.2 norm gamma/beta at 1.15 times W0 on round 5 lexical background. Other merger norms W0. Tests stronger third auxiliary visual signal after attenuation harmed counterfactual visual judgments.

**本轮原记录的主分数**：`0.69140625`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-38556e573c8e807ed1082d80027a1089e3deb0cb15d7ffc11de74337db726fad",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.69140625
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 18398,
  "id": "c-38556e573c8e807ed1082d80027a1089e3deb0cb15d7ffc11de74337db726fad",
  "l2": 9.849813856580864,
  "parent": "c-a428b61111165b3f6628c0e0f482bb6d3497135ab9bb3516d26ffc6354c9708f",
  "rationale": "Round 16: isolate deepstack_merger_list.2 norm gamma/beta at 1.15 times W0 on round 5 lexical background. Other merger norms W0. Tests stronger third auxiliary visual signal after attenuation harmed counterfactual visual judgments.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-38556e573c8e807ed1082d80027a1089e3deb0cb15d7ffc11de74337db726fad",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.9015625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 61,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 51,
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
        "correct": 57,
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
    "primary_joint": 0.75,
    "repair_score": 0.69140625,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第17轮

**当时目的与操作理由（原文）**

Round 17: combine round 9 main-merger norm gamma/beta at 0.85 times W0 with round 16 deepstack_merger_list.2 norm gamma/beta at 1.15 times W0. Keep round 5 lexical embeddings and other merger norms unchanged at W0. Tests complementary usual-scope and visual-scope improvements, without assuming additive effects.

**本轮原记录的主分数**：`0.69921875`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-554e69bda62793032a2aef09107692bff225e29f0d2161f3936e7869899358e5",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.69921875
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 20446,
  "id": "c-554e69bda62793032a2aef09107692bff225e29f0d2161f3936e7869899358e5",
  "l2": 11.843175484130425,
  "parent": "c-38556e573c8e807ed1082d80027a1089e3deb0cb15d7ffc11de74337db726fad",
  "rationale": "Round 17: combine round 9 main-merger norm gamma/beta at 0.85 times W0 with round 16 deepstack_merger_list.2 norm gamma/beta at 1.15 times W0. Keep round 5 lexical embeddings and other merger norms unchanged at W0. Tests complementary usual-scope and visual-scope improvements, without assuming additive effects.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-554e69bda62793032a2aef09107692bff225e29f0d2161f3936e7869899358e5",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.901953125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 39,
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
        "correct": 50,
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
        "correct": 57,
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
    "primary_joint": 0.75,
    "repair_score": 0.69921875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第18轮

**当时目的与操作理由（原文）**

Round 18: retain round 17 lexical and visual-merger combination; set decoder layers 0-5 input_layernorm.weight to 0.9 times W0, with all other decoder input norms at W0. Tests early decoder evidence-integration gain, including no-image scope/order errors. This broad sensitivity intervention does not assert a localized defect.

**本轮原记录的主分数**：`0.6953125`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-52f209bfb1c1cfa86f5d3bd8012a6fe1581e3248deba22b9df0e29d04c6b7eb7",
  "l2": 11.898170755481264,
  "parent": "c-554e69bda62793032a2aef09107692bff225e29f0d2161f3936e7869899358e5",
  "rationale": "Round 18: retain round 17 lexical and visual-merger combination; set decoder layers 0-5 input_layernorm.weight to 0.9 times W0, with all other decoder input norms at W0. Tests early decoder evidence-integration gain, including no-image scope/order errors. This broad sensitivity intervention does not assert a localized defect.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.0.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d18dd9237fbce1c611e0670d5dc757a1114e93f07606cee8784f5f40b4b52827.npy",
      "sha256": "bec339f9a046c2ed6e01e3169ef8454083656a488b7c4f58ff94287aae845467",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.1.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "fd3e9aa3b5190792e2ae5feef960d00afc5193c99cec0c0db3f885e7aa72e2b7.npy",
      "sha256": "0311742ed40888f941324ad754659997512848270f693b0d872b50c7255dd2b8",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.2.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "2041d4454b8cb67836330a465afa84171c935b14d3f642335bfe5bdb1dfb6dca.npy",
      "sha256": "425f3d3669a100681b468797db25f5eb996406191f790567264f0ba7092715e6",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.3.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "cd4dfb87bdab3a4debfa21083312ef29e3495826d2e18d81b5218a0663d423f7.npy",
      "sha256": "41aceac949387b9668c04b2fe24c8d45f4cab951cc91aede2467960a4a02a986",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.4.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ff04d1b5ea28422154ae4f5b782bcde2feeae34288830517b710a0ca68f2e3aa.npy",
      "sha256": "18657b7ceeee6790a516ec8c2adbd04a2fbd99edc121645a9c851e4ee96ba639",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.5.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "dcaee351d2e3be283dd14c3a6de58ba5936cd200433f1dd8306a5412ecb0defb.npy",
      "sha256": "2576548aeda6967ec02b8aefcd190ab3ab3b61e8c4c3fd250f2af2ed3190434d",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-52f209bfb1c1cfa86f5d3bd8012a6fe1581e3248deba22b9df0e29d04c6b7eb7",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.90078125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 61,
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
        "correct": 60,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 52,
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
        "correct": 46,
        "n": 64
      },
      "B1:T1:1:counterfact_visual": {
        "correct": 56,
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
    "primary_joint": 0.75,
    "repair_score": 0.6953125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第19轮

**当时目的与操作理由（原文）**

Round 19: fixed round 17 lexical/visual background; decoder layers 0-5 input_layernorm.weight at 1.1 times W0 rather than round 18's 0.9. All other decoder input norms remain W0. Opposing-sign test of early evidence-integration gain after attenuation caused mixed no-image changes and a visual-control loss.

**本轮原记录的主分数**：`0.69921875`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-b178ff20ecc90076a232a46d6179506d50220e1e00db5dd56196c70ed2673d31",
  "l2": 11.898219033136758,
  "parent": "c-52f209bfb1c1cfa86f5d3bd8012a6fe1581e3248deba22b9df0e29d04c6b7eb7",
  "rationale": "Round 19: fixed round 17 lexical/visual background; decoder layers 0-5 input_layernorm.weight at 1.1 times W0 rather than round 18's 0.9. All other decoder input norms remain W0. Opposing-sign test of early evidence-integration gain after attenuation caused mixed no-image changes and a visual-control loss.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.0.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d18dd9237fbce1c611e0670d5dc757a1114e93f07606cee8784f5f40b4b52827.npy",
      "sha256": "fc086da834082b7da9ecbe9b9590be2e27131042fe8fbb3cdc60d72c123586f2",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.1.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "fd3e9aa3b5190792e2ae5feef960d00afc5193c99cec0c0db3f885e7aa72e2b7.npy",
      "sha256": "a58cd4df32749b8aa79b9af8637f6c57d993f93f6654ffdae2d9a7b04c619e3d",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.2.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "2041d4454b8cb67836330a465afa84171c935b14d3f642335bfe5bdb1dfb6dca.npy",
      "sha256": "2783bb6ac4ffa8230b98fc18ace0250a402fb05e6e7ddbaea36da2218907fb73",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.3.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "cd4dfb87bdab3a4debfa21083312ef29e3495826d2e18d81b5218a0663d423f7.npy",
      "sha256": "174f862a99e1f7a04c0f1051c4b0b988854d183c1b66a856a4b932bdd1378d53",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.4.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ff04d1b5ea28422154ae4f5b782bcde2feeae34288830517b710a0ca68f2e3aa.npy",
      "sha256": "f6b861bab09e45601d6e8f8d526f3ef9f0f90efc5da44e0340a677a808908f0b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.5.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "dcaee351d2e3be283dd14c3a6de58ba5936cd200433f1dd8306a5412ecb0defb.npy",
      "sha256": "254a12176e30d2c873aec4c8d83ea0e6057706c1d60111b25f2b6b1853d881dd",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-b178ff20ecc90076a232a46d6179506d50220e1e00db5dd56196c70ed2673d31",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.901953125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 59,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 62,
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
        "correct": 50,
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
        "correct": 54,
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
    "primary_joint": 0.75,
    "repair_score": 0.69921875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第20轮

**当时目的与操作理由（原文）**

Round 20: keep the round 17 lexical/visual background; restore layers 0-5 input norms to W0 and scale only layers 6-11 input_layernorm.weight to 0.9 times W0. Tests depth-specific attenuation after neither early-layer direction improved the selection score.

**本轮原记录的主分数**：`0.6796875`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-cb48046ac46aa9b9af1dcd9510678e9c829fb1092fe8dd98f2bba43cc0946c2a",
  "l2": 12.444516923553733,
  "parent": "c-b178ff20ecc90076a232a46d6179506d50220e1e00db5dd56196c70ed2673d31",
  "rationale": "Round 20: keep the round 17 lexical/visual background; restore layers 0-5 input norms to W0 and scale only layers 6-11 input_layernorm.weight to 0.9 times W0. Tests depth-specific attenuation after neither early-layer direction improved the selection score.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.10.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "be51ed205846ee9a9c982167849036e69006b9e00850109327d635661ab78ccc.npy",
      "sha256": "2ed165fa433de18d900483223787f4508fa1f27e4dc9eae047409db2f1ad5b20",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.11.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9568b66aace3a337c5a4854a52f6e6e02b588427d51e03b4bcc0fb6aa7a64c15.npy",
      "sha256": "ebd75ef5ac8790a31c102f595a1d690e2035970ceeaf33b8b94e31e6bf8caeca",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.6.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "a77610fc64d9b424a57f354ea0bdba6b0bec5fd72a905fbedcfe925f67a21444.npy",
      "sha256": "d810c3970a8a07c167f6db9dcfbcb9c0f6ed75e8cdf61dbb752616b01908a340",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.7.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9490e60c38d1921c8a81f4c739bc1c90f71ab5625261ca7e8d1f85eaadf1a3e6.npy",
      "sha256": "126aedc52fbfa6dd0727b043ea4e9ab9d8d918ef19a69d2943d2234b1b119004",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.8.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "c396451620f69374637b8457e14d0c0d26998019f898f139eac2bc3c56c68fb0.npy",
      "sha256": "1e5d1801261d46eb3ed47484428b9b05dbdbee68948de982582a7e3210f043a5",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.9.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d0c7da330504e50b90dd3d9783542418f8b6c45c1256c9adff687e49a7be9dfb.npy",
      "sha256": "b7fe9225d7d4705177e2efe537c763ffef763d0edf69f75b51bf0620616040e0",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-cb48046ac46aa9b9af1dcd9510678e9c829fb1092fe8dd98f2bba43cc0946c2a",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.900390625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 53,
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
        "correct": 62,
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
        "correct": 56,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 51,
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
        "correct": 55,
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
    "primary_joint": 0.734375,
    "repair_score": 0.6796875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第21轮

**当时目的与操作理由（原文）**

Round 21: fixed round 17 lexical/visual background; scale only layers 6-11 input_layernorm.weight to 1.1 times W0, restoring all other decoder input norms to W0. Tests the opposite direction after attenuation disproportionately reduced B0 counterfactual-usual accuracy.

**本轮原记录的主分数**：`0.69140625`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-50f9b2a9c196364615b565a8d4dead50f542483c1bf5d51be4a8d0116c4aded5",
  "l2": 12.444865275729514,
  "parent": "c-cb48046ac46aa9b9af1dcd9510678e9c829fb1092fe8dd98f2bba43cc0946c2a",
  "rationale": "Round 21: fixed round 17 lexical/visual background; scale only layers 6-11 input_layernorm.weight to 1.1 times W0, restoring all other decoder input norms to W0. Tests the opposite direction after attenuation disproportionately reduced B0 counterfactual-usual accuracy.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.10.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "be51ed205846ee9a9c982167849036e69006b9e00850109327d635661ab78ccc.npy",
      "sha256": "ba0a462f1fc02108f02ba7d33e4c26e2257c1c6bd1919b87c053fcec947b7d65",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.11.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9568b66aace3a337c5a4854a52f6e6e02b588427d51e03b4bcc0fb6aa7a64c15.npy",
      "sha256": "2df9d17bbfee40b2fc417d950c93afc2684790b6465e8aeb0a33c398157d10b0",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.6.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "a77610fc64d9b424a57f354ea0bdba6b0bec5fd72a905fbedcfe925f67a21444.npy",
      "sha256": "025ee36b93d45fa891ac4edfe8323f072076ac80864de69a70c1a55181be9679",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.7.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9490e60c38d1921c8a81f4c739bc1c90f71ab5625261ca7e8d1f85eaadf1a3e6.npy",
      "sha256": "5a50737cbab74a61a9dbabfc856a0131f43b54dc3375fbbf8051a8d5a0b0ad24",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.8.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "c396451620f69374637b8457e14d0c0d26998019f898f139eac2bc3c56c68fb0.npy",
      "sha256": "5dc420515274495cd7f9c0467d2fe0c866798debe85c9e33d96552b1955ded97",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.9.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d0c7da330504e50b90dd3d9783542418f8b6c45c1256c9adff687e49a7be9dfb.npy",
      "sha256": "2960b032204ad13a941a1407016f5157439686b87dc3c920592854703e40959f",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-50f9b2a9c196364615b565a8d4dead50f542483c1bf5d51be4a8d0116c4aded5",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.899609375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
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
        "correct": 62,
        "n": 64
      },
      "B0:T0:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:0:counterfact_usual": {
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 39,
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
        "correct": 51,
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
    "repair_score": 0.69140625,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第22轮

**当时目的与操作理由（原文）**

Round 22: fixed round 17 lexical/visual background; only decoder layers 12-17 input_layernorm.weight scaled to 0.9 times W0. Restore all other decoder input norms to W0. Tests middle-depth attention-input calibration independently of the earlier bands.

**本轮原记录的主分数**：`0.69140625`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-b319968466a897a58ee7b242b76b9be4171c39c84197432fa469751b3fff0899",
  "l2": 13.181602513041573,
  "parent": "c-50f9b2a9c196364615b565a8d4dead50f542483c1bf5d51be4a8d0116c4aded5",
  "rationale": "Round 22: fixed round 17 lexical/visual background; only decoder layers 12-17 input_layernorm.weight scaled to 0.9 times W0. Restore all other decoder input norms to W0. Tests middle-depth attention-input calibration independently of the earlier bands.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.12.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "e57f2ba1dd92e4a12b6cb857f22dae6a82f8de0b8703535bc51543485e079b22.npy",
      "sha256": "2b3cad2bfb725ba639beb63e762967ed802e964f2aa3d9db249cd007115c53c8",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.13.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "028ac9c30d8e1e9060986a456afde270a51d39a590ec017f0a8af6971f6a9539.npy",
      "sha256": "949a472f631c44e5f8dc7b435f23a9f7171e19496fe0e2cbd31381f028fc2f09",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.14.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "81723cc2bda8566eca79b387adb6a32f9a1657b727b93cd3e6c1ec56cee125d7.npy",
      "sha256": "2acb8b823b109acbebca5b5efa5ab1006ea1b464fcc9035882b24cb68b8b0abb",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.15.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f5048c39ae1fe62ea97fcc03d65cf73c355d27080918af6be3bcd045d9053a43.npy",
      "sha256": "c71432c5aec328e8ac46511e03b2bbff91a10e68ca3ce01b5b13b719897377f8",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.16.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b2561341cf7a992be6fe49fecf46a8e3be0de6e1d3009aab60a7b5ccdbb671a4.npy",
      "sha256": "31a297f0c08deda5e40ff3d11f71a07349194cccd90544f9cfdccdf6cee991cf",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.17.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "18f1395b23d1597948224b434838c9d3c6ea490a90322537b8b3e68a8426c7ed.npy",
      "sha256": "31eec85f96433b8780d98f8eae7f705e033a0a00e978f9e72ec7b08711dfcef0",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-b319968466a897a58ee7b242b76b9be4171c39c84197432fa469751b3fff0899",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.90234375,
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
        "correct": 46,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
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
        "correct": 51,
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
        "correct": 56,
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
    "primary_joint": 0.75,
    "repair_score": 0.69140625,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第23轮

**当时目的与操作理由（原文）**

Round 23: retain the fixed round 17 lexical/visual background and scale only layers 12-17 input_layernorm.weight to 1.1 times W0. All other decoder input norms are W0. Opposing-sign test of the visual-versus-usual tradeoff observed with middle-depth attenuation.

**本轮原记录的主分数**：`0.69140625`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-813d5c078caccac27bf1ec59a6de08d951da17baa275d3faccb2845d8d095ed5",
  "l2": 13.18258660661143,
  "parent": "c-b319968466a897a58ee7b242b76b9be4171c39c84197432fa469751b3fff0899",
  "rationale": "Round 23: retain the fixed round 17 lexical/visual background and scale only layers 12-17 input_layernorm.weight to 1.1 times W0. All other decoder input norms are W0. Opposing-sign test of the visual-versus-usual tradeoff observed with middle-depth attenuation.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.12.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "e57f2ba1dd92e4a12b6cb857f22dae6a82f8de0b8703535bc51543485e079b22.npy",
      "sha256": "cabbc52522c605ef72bc2dd6d9c6472c8a3b296a27994153c77b61cfa0eb3250",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.13.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "028ac9c30d8e1e9060986a456afde270a51d39a590ec017f0a8af6971f6a9539.npy",
      "sha256": "5800b9074d03f0d2547397dcee77b0bf277b5369841aa181954d0773da7ec0a6",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.14.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "81723cc2bda8566eca79b387adb6a32f9a1657b727b93cd3e6c1ec56cee125d7.npy",
      "sha256": "b4799df498cdbc813ffe4279cf9df068e1b2194d246bc7c46ff226911979487e",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.15.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f5048c39ae1fe62ea97fcc03d65cf73c355d27080918af6be3bcd045d9053a43.npy",
      "sha256": "81945198f63968f5e01008a1122a591895e2ca8f96f11ce24f38682e062aa829",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.16.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b2561341cf7a992be6fe49fecf46a8e3be0de6e1d3009aab60a7b5ccdbb671a4.npy",
      "sha256": "4934a1be1e33ec956df9ef3044605c79fa18a408a72aebc04da71d437c1303fe",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.17.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "18f1395b23d1597948224b434838c9d3c6ea490a90322537b8b3e68a8426c7ed.npy",
      "sha256": "fc8dcc69198f8e9a8ca1f9f599b492be413743a0ef25162fc681fdacdf15ef6d",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-813d5c078caccac27bf1ec59a6de08d951da17baa275d3faccb2845d8d095ed5",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.9015625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 53,
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
        "correct": 41,
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
        "correct": 56,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 50,
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
        "correct": 54,
        "n": 64
      },
      "B1:T1:1:no_image_usual": {
        "correct": 53,
        "n": 64
      },
      "B1:T1:1:original_usual": {
        "correct": 61,
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
    "repair_score": 0.69140625,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第24轮

**当时目的与操作理由（原文）**

Round 24: retain the fixed round 17 lexical/visual background; scale only decoder layers 18-23 input_layernorm.weight to 0.9 times W0 and restore all other decoder input norms to W0. Tests depth-specific sensitivity after neither direction in layers 12-17 improved the selection score.

**本轮原记录的主分数**：`0.6953125`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-6cef137b212d626e6c8f378008cca635f1b5b74d19ade7a51b79cf18a03243a9",
  "l2": 15.53808728972393,
  "parent": "c-813d5c078caccac27bf1ec59a6de08d951da17baa275d3faccb2845d8d095ed5",
  "rationale": "Round 24: retain the fixed round 17 lexical/visual background; scale only decoder layers 18-23 input_layernorm.weight to 0.9 times W0 and restore all other decoder input norms to W0. Tests depth-specific sensitivity after neither direction in layers 12-17 improved the selection score.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "b373b70aa5e869eae2699220ac0a82a312495fd6fe53ca001000d3dae8e51e2e",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "3a888cf0b1e05767d5900e673eb962fe2024c541508c70a401dc5ab176d96d19",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "f20a5089664e30e6724628eb978f597e42a0903f987bfe4bc70526f7cbcb558b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "0dccd513679541cc7019fbb626468365e2bd4a3c8a01a4d352fc5ad9e9c5f2b1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "181b3b573e7a5e87c832f955ea0a8d5bcc613c05509d7d630344b47514332064",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "96f4e2f07911a3daf8d5d2187b167cd7b010780a107e106f20e79f77b8dd8751",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-6cef137b212d626e6c8f378008cca635f1b5b74d19ade7a51b79cf18a03243a9",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.902734375,
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
        "correct": 46,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 41,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
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
        "correct": 51,
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
        "correct": 54,
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
    "primary_joint": 0.734375,
    "repair_score": 0.6953125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第25轮

**当时目的与操作理由（原文）**

Round 25: fixed round 17 lexical/visual background; scale only decoder layers 18-23 input_layernorm.weight to 1.1 times W0, with all other decoder input norms restored to W0. Opposing-sign test after attenuation improved aggregate accuracy but lost B0 counterfactual-usual answers and did not improve the joint selection score.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-a7b3f4294e2a6b9ae660cb03872acc57607a067767099e6823184c3974a25844",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.703125
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 35806,
  "id": "c-a7b3f4294e2a6b9ae660cb03872acc57607a067767099e6823184c3974a25844",
  "l2": 15.538648017758636,
  "parent": "c-6cef137b212d626e6c8f378008cca635f1b5b74d19ade7a51b79cf18a03243a9",
  "rationale": "Round 25: fixed round 17 lexical/visual background; scale only decoder layers 18-23 input_layernorm.weight to 1.1 times W0, with all other decoder input norms restored to W0. Opposing-sign test after attenuation improved aggregate accuracy but lost B0 counterfactual-usual answers and did not improve the joint selection score.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "19a2097aa713a4dde0c4744fe3023c6ea85b17d5e0ffc9a9c40e5241ac26076a",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "d69b610c06bb2c90af96d798d500c47f174f79e8fcd2c2d7d671db26e872b595",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "069d6dae7e99c98015b955f97da543fe192c20bfcf9b13174d9acaa260466905",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "b0d14e70201e61f9994dce1cb45642ae5eb6cd45ab5b303cdb324684925e65df",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "6091554c92fe5d44c6ddc8340225e84cea2152d05287a3728b5c259e9459bdcc",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "1b0fed998da636c8651d7beb9a49d64111c6b5ec5f029d4d38b68a8ce025fb4e",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-a7b3f4294e2a6b9ae660cb03872acc57607a067767099e6823184c3974a25844",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.900390625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 51,
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
        "correct": 57,
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
    "primary_joint": 0.765625,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第26轮

**当时目的与操作理由（原文）**

Round 26: retain round 17 lexical/visual weights, restore layers 18-23 input norms to W0, and scale only layers 24-29 input_layernorm.weight to 0.9 times W0. Tests a later decoder band independently; round 25's small joint-score gain is not assumed to compose with this intervention.

**本轮原记录的主分数**：`0.69921875`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-657d316ab3b4775d8f5fcd271db896dd5f8e182f366fdf7b112cb880168fab85",
  "l2": 20.811232850462268,
  "parent": "c-a7b3f4294e2a6b9ae660cb03872acc57607a067767099e6823184c3974a25844",
  "rationale": "Round 26: retain round 17 lexical/visual weights, restore layers 18-23 input norms to W0, and scale only layers 24-29 input_layernorm.weight to 0.9 times W0. Tests a later decoder band independently; round 25's small joint-score gain is not assumed to compose with this intervention.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.24.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "77c4613931768505df997ce35b185e0dec3d9b63fec702daca9e24a812cda5e8.npy",
      "sha256": "4af849c5c8642dd5ce365480b9f9045ba9661a2da11a8017984a80e24ced43d4",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.25.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "e1f2d75301b0239b67de3d5506e60b87a476aa5d6f104b962f96cbc4a9162d8b.npy",
      "sha256": "6a0f453e2aa8b183460dca494b618b8f1ad53498d74ffeee33986dc1a34038b0",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.26.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "2eb33f76dd51fb6e368619709c6f05a3dcc52ebd72613ac5234565e1ec13d9f3.npy",
      "sha256": "84859682654dcb295f8d07460bf3852ff65b20331778ace574d5091feb068089",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.27.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "cf0da2baa7c2cc746e3d639c1dac91e19c70c1c38d3159c87472d99022d21623.npy",
      "sha256": "7c0cf1bb20d3d439908d10f7862af338d905defb926b3ba64dcc8da058c2f3da",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.28.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "272f5d5c67bfd66f9630b60728c98a90261b9cdde8d4d048f075d2541e852d0f.npy",
      "sha256": "cb3722bbecaacf2ec77fce490e4d51c269c9f064cd719839a9d18add19fe2b70",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.29.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ba737a40b2362b80d594e00d2d0c976def3c6197584bfe68ae5c8cc6a67ced77.npy",
      "sha256": "e7189844eb032626dd5877123fed3799bc4bd4e7957d5f36e9d8c828b2a61a00",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-657d316ab3b4775d8f5fcd271db896dd5f8e182f366fdf7b112cb880168fab85",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.901953125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 39,
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
        "correct": 50,
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
        "correct": 55,
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
    "primary_joint": 0.75,
    "repair_score": 0.69921875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第27轮

**当时目的与操作理由（原文）**

Round 27: fixed round 17 lexical/visual background; scale only decoder layers 24-29 input_layernorm.weight to 1.1 times W0 and restore all other decoder input norms to W0. Opposing-sign test after attenuation left the selection score unchanged while altering a no-image answer and B1 counterfactual judgments.

**本轮原记录的主分数**：`0.69921875`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-f47bdd400b5428fff7b1281f0b5dcfefef2b45ffe487d5604e0c5a2b401cd926",
  "l2": 20.810806215531112,
  "parent": "c-657d316ab3b4775d8f5fcd271db896dd5f8e182f366fdf7b112cb880168fab85",
  "rationale": "Round 27: fixed round 17 lexical/visual background; scale only decoder layers 24-29 input_layernorm.weight to 1.1 times W0 and restore all other decoder input norms to W0. Opposing-sign test after attenuation left the selection score unchanged while altering a no-image answer and B1 counterfactual judgments.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.24.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "77c4613931768505df997ce35b185e0dec3d9b63fec702daca9e24a812cda5e8.npy",
      "sha256": "22bc8002e000f975623fff7c5040c2d0598f90c28e5278687e395687c4730213",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.25.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "e1f2d75301b0239b67de3d5506e60b87a476aa5d6f104b962f96cbc4a9162d8b.npy",
      "sha256": "bdd8ed2247cc84207c9641bb32bd11c7a5c323b0136057d5706e8787d9791a20",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.26.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "2eb33f76dd51fb6e368619709c6f05a3dcc52ebd72613ac5234565e1ec13d9f3.npy",
      "sha256": "5774fb64609746f024c341b24f6345a0c0c30758dad1a3465a4ec73cb1447d50",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.27.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "cf0da2baa7c2cc746e3d639c1dac91e19c70c1c38d3159c87472d99022d21623.npy",
      "sha256": "4c5c05063350978a035ba13a8e94d5b0561e9f26844bbe4b684cd8028c68dc81",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.28.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "272f5d5c67bfd66f9630b60728c98a90261b9cdde8d4d048f075d2541e852d0f.npy",
      "sha256": "93b8fab087b0243d36900a2521b5f80afa472711ad28b64e0a956e8f3d05e19b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.29.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ba737a40b2362b80d594e00d2d0c976def3c6197584bfe68ae5c8cc6a67ced77.npy",
      "sha256": "ff239dc680eb9a46ffb9188f47e4251b22308f8468a1fe31ba0d6d9756dfd4ab",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f47bdd400b5428fff7b1281f0b5dcfefef2b45ffe487d5604e0c5a2b401cd926",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.902734375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 40,
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
        "correct": 51,
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
        "correct": 57,
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
    "primary_joint": 0.75,
    "repair_score": 0.69921875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第28轮

**当时目的与操作理由（原文）**

Round 28: fixed round 17 lexical/visual background; scale only decoder layers 30-35 input_layernorm.weight to 0.9 times W0 and restore all other decoder input norms to W0. Tests final-depth attention-input sensitivity after neither direction in layers 24-29 improved the B0 joint selection score.

**本轮原记录的主分数**：`0.69921875`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-61fef4766ecc443c392f2dac42321acfe643a4185587621d409d154e7e8279a2",
  "l2": 47.6798259758794,
  "parent": "c-f47bdd400b5428fff7b1281f0b5dcfefef2b45ffe487d5604e0c5a2b401cd926",
  "rationale": "Round 28: fixed round 17 lexical/visual background; scale only decoder layers 30-35 input_layernorm.weight to 0.9 times W0 and restore all other decoder input norms to W0. Tests final-depth attention-input sensitivity after neither direction in layers 24-29 improved the B0 joint selection score.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.30.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "8a3aaeef9a9cbbe5940270bbb9121ff794bf62a2e95ad636d84a1faea80dfa13.npy",
      "sha256": "ec21b25a6620b5d5e3d4a72e082651bcbfc65f6756950b4bcc83965558d01f2f",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.31.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f22ed3e0610b87f05c103e551e925c979d409b3c12d24a82b99aef5e28441bf6.npy",
      "sha256": "d8feb0939bd22db5f1a7d0f713275971053555c2c3d1421b83eab385a3377deb",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.32.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "423da1a777e819de9f2787aa3fb1264904059a69f2a11a4c04a9c1656a296397.npy",
      "sha256": "805994305d00ac648b6b86d6b0fe974b6dee7a795eb2de8d8ea36eb5f1cd5e5a",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.33.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9097eac7d3276829df5def659aca29ed0a97b4370f5cc86ae93ce0875c89b002.npy",
      "sha256": "078264d210f93c48ad269ac07d1064cd9e12d6233927d6b0c4e852940e654edd",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.34.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "4b3c31b7ed083725bcbf2b081923f6c2cf83690bbc897c72e70754ac1d2acb05.npy",
      "sha256": "dedfc21df4334b9cdad978dc8a37f5d7c47a0a90e1b0c2a91a086559826b856f",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.35.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9e354f42aa507c300b7e80d2c41384682ac4ecb666f0aecdac7e0d870b295c94.npy",
      "sha256": "cec5d8ecce1fcb2dd2a5e6b6b7c410c944f9b02de3bbf9c32a660af17f7345d4",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-61fef4766ecc443c392f2dac42321acfe643a4185587621d409d154e7e8279a2",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.90234375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 39,
        "n": 64
      },
      "B1:T0:1:counterfact_visual": {
        "correct": 62,
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
        "correct": 51,
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
        "correct": 57,
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
    "primary_joint": 0.75,
    "repair_score": 0.69921875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第29轮

**当时目的与操作理由（原文）**

Round 29: fixed round 17 lexical/visual background; scale only decoder layers 30-35 input_layernorm.weight to 1.1 times W0, restoring all other decoder input norms to W0. Completes the opposing-sign depth sweep after final-band attenuation left B0 joint correctness unchanged and caused two no-image regressions versus round 17.

**本轮原记录的主分数**：`0.69921875`；保留原始0–1尺度。

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
  "changed_scalars": 35806,
  "id": "c-ca3d346a92207de5d53d8b74a222a01ffadc8d5cc02208aecf8539bfab81299e",
  "l2": 47.65906040035243,
  "parent": "c-61fef4766ecc443c392f2dac42321acfe643a4185587621d409d154e7e8279a2",
  "rationale": "Round 29: fixed round 17 lexical/visual background; scale only decoder layers 30-35 input_layernorm.weight to 1.1 times W0, restoring all other decoder input norms to W0. Completes the opposing-sign depth sweep after final-band attenuation left B0 joint correctness unchanged and caused two no-image regressions versus round 17.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.30.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "8a3aaeef9a9cbbe5940270bbb9121ff794bf62a2e95ad636d84a1faea80dfa13.npy",
      "sha256": "a38948445d9408fc445586e7b935869c804fcd6bbd5cd8f6d378e0506919b5b9",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.31.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f22ed3e0610b87f05c103e551e925c979d409b3c12d24a82b99aef5e28441bf6.npy",
      "sha256": "2d1078f6ef58185e9cdd80a7a4da96f8f65e14f318c7fa365ff4b843ea5b460a",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.32.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "423da1a777e819de9f2787aa3fb1264904059a69f2a11a4c04a9c1656a296397.npy",
      "sha256": "8e32069610871bdbaa8678dbb3486c2286dadd9bdd4820b14b3d7ceb9be033cb",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.33.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9097eac7d3276829df5def659aca29ed0a97b4370f5cc86ae93ce0875c89b002.npy",
      "sha256": "991388d8626926bf706823dbe310f195bd404ed7f4c982dbd29ad91f3e9adf8f",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.34.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "4b3c31b7ed083725bcbf2b081923f6c2cf83690bbc897c72e70754ac1d2acb05.npy",
      "sha256": "96ed212983703026cadeaaeeb8c093a13d3770a409df0ec2d48cc7f8ad928860",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.35.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9e354f42aa507c300b7e80d2c41384682ac4ecb666f0aecdac7e0d870b295c94.npy",
      "sha256": "2d79098983c5ab61b1c34985780f65cbda2d3d5f67fed3fa51de3cfd4f72bd27",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-ca3d346a92207de5d53d8b74a222a01ffadc8d5cc02208aecf8539bfab81299e",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.903125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 39,
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
        "correct": 50,
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
        "correct": 56,
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
    "primary_joint": 0.75,
    "repair_score": 0.69921875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第30轮

**当时目的与操作理由（原文）**

Round 30: retain the fixed round 17 lexical/visual background; scale only decoder layers 18-23 input_layernorm.weight to 1.05 times W0 and restore all other decoder input norms to W0. Tests a smaller positive gain after round 25's 1.1 gain improved the selection score by one joint pair but introduced control regressions. Final distinct repair candidate; evaluate on the unchanged full development pack.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-5e294d20824422390149f1b3d7d8f2242abd1fd57d6eea3d521ba43da9270e78",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.703125
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 35806,
  "id": "c-5e294d20824422390149f1b3d7d8f2242abd1fd57d6eea3d521ba43da9270e78",
  "l2": 12.86790827696188,
  "parent": "c-ca3d346a92207de5d53d8b74a222a01ffadc8d5cc02208aecf8539bfab81299e",
  "rationale": "Round 30: retain the fixed round 17 lexical/visual background; scale only decoder layers 18-23 input_layernorm.weight to 1.05 times W0 and restore all other decoder input norms to W0. Tests a smaller positive gain after round 25's 1.1 gain improved the selection score by one joint pair but introduced control regressions. Final distinct repair candidate; evaluate on the unchanged full development pack.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10206,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "cc4c2016e1a2399a4b8db6050f8ffedc15f32ad5fa43fee7a037d371d0c5c0ec",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-5e294d20824422390149f1b3d7d8f2242abd1fd57d6eea3d521ba43da9270e78",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.9015625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 57,
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
    "primary_joint": 0.765625,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第31轮

**当时目的与操作理由（原文）**

Round 31 of 50: reduce the norm-preserving pictured-to-image embedding mixture from alpha 0.5 to 0.25. Keep the other three lexical mixtures, visual merger norms, and decoder layers 18-23 input-norm gain at the round 30 configuration. Tests whether weaker lexical alignment improves scope-sensitive joint correctness without additional control losses.

**本轮原记录的主分数**：`0.67578125`；保留原始0–1尺度。

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
  "changed_scalars": 35797,
  "id": "c-d78f6e8b9d708bfe20d1c3295478df377383889b27886f2efb53aab7bd5b7ed6",
  "l2": 12.846607766712443,
  "parent": "c-5e294d20824422390149f1b3d7d8f2242abd1fd57d6eea3d521ba43da9270e78",
  "rationale": "Round 31 of 50: reduce the norm-preserving pictured-to-image embedding mixture from alpha 0.5 to 0.25. Keep the other three lexical mixtures, visual merger norms, and decoder layers 18-23 input-norm gain at the round 30 configuration. Tests whether weaker lexical alignment improves scope-sensitive joint correctness without additional control losses.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10197,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "0d9f73b9c5fd44224d84df4c8fad721fdaa552d30722de1dd7f6b4ee3f2301d2",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-d78f6e8b9d708bfe20d1c3295478df377383889b27886f2efb53aab7bd5b7ed6",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.898046875,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 46,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 51,
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
        "correct": 55,
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
    "primary_joint": 0.765625,
    "repair_score": 0.67578125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第32轮

**当时目的与操作理由（原文）**

Round 32 of 50: set the norm-preserving pictured-to-image mixture to alpha 0.75, with bigger-to-larger, normally-to-typically, and -world-to-world each at 0.5. Retain round 30 visual norms and decoder layers 18-23 input-norm gain 1.05. Complements round 31's weaker-mixture test, which reduced the joint score through visual regressions.

**本轮原记录的主分数**：`0.6953125`；保留原始0–1尺度。

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
  "changed_scalars": 35809,
  "id": "c-abd932022327c69976b0e468206b44594d83c9c20b9dd7b28d5192a7ebddcf1d",
  "l2": 12.902516114457292,
  "parent": "c-d78f6e8b9d708bfe20d1c3295478df377383889b27886f2efb53aab7bd5b7ed6",
  "rationale": "Round 32 of 50: set the norm-preserving pictured-to-image mixture to alpha 0.75, with bigger-to-larger, normally-to-typically, and -world-to-world each at 0.5. Retain round 30 visual norms and decoder layers 18-23 input-norm gain 1.05. Complements round 31's weaker-mixture test, which reduced the joint score through visual regressions.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10209,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "d9d8eb459634aea8e0ce7d4263d29ca29038956c3c3b9f55eb0e71a76b1508ae",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-abd932022327c69976b0e468206b44594d83c9c20b9dd7b28d5192a7ebddcf1d",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.899609375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 55,
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
    "primary_joint": 0.765625,
    "repair_score": 0.6953125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第33轮

**当时目的与操作理由（原文）**

Round 33 of 50: restore pictured-to-image alpha 0.5 and set bigger-to-larger alpha 0.25; normally-to-typically and -world-to-world remain 0.5. All nonembedding weights retain the round 30 configuration. Tests weaker comparison-word alignment independently after both pictured-mixture alternatives underperformed.

**本轮原记录的主分数**：`0.69921875`；保留原始0–1尺度。

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
  "changed_scalars": 35789,
  "id": "c-5e38c756bd5d7d65a01d5a0e5ba95f12734d299b7912d7531cdce70a96da3301",
  "l2": 12.861157521907073,
  "parent": "c-abd932022327c69976b0e468206b44594d83c9c20b9dd7b28d5192a7ebddcf1d",
  "rationale": "Round 33 of 50: restore pictured-to-image alpha 0.5 and set bigger-to-larger alpha 0.25; normally-to-typically and -world-to-world remain 0.5. All nonembedding weights retain the round 30 configuration. Tests weaker comparison-word alignment independently after both pictured-mixture alternatives underperformed.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10189,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "7fae92e3232e3c527e71f649ee1800e6db0b936158a8965e3631d9dc8a056e9b",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-5e38c756bd5d7d65a01d5a0e5ba95f12734d299b7912d7531cdce70a96da3301",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.899609375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 53,
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
    "primary_joint": 0.765625,
    "repair_score": 0.69921875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第34轮

**当时目的与操作理由（原文）**

Round 34 of 50: set the norm-preserving bigger-to-larger mixture to alpha 0.75; pictured-to-image, normally-to-typically, and -world-to-world remain 0.5. Preserve all round 30 nonembedding weights. Tests stronger comparison-word alignment after alpha 0.25 produced only regressions relative to round 30.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

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
  "changed_scalars": 35807,
  "id": "c-75576402e12e975be45c7df8aedc68ee1d65a2991153409c6ff0b2eda5707bcd",
  "l2": 12.879077071867298,
  "parent": "c-5e38c756bd5d7d65a01d5a0e5ba95f12734d299b7912d7531cdce70a96da3301",
  "rationale": "Round 34 of 50: set the norm-preserving bigger-to-larger mixture to alpha 0.75; pictured-to-image, normally-to-typically, and -world-to-world remain 0.5. Preserve all round 30 nonembedding weights. Tests stronger comparison-word alignment after alpha 0.25 produced only regressions relative to round 30.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10207,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "e9837b2d351feff366144faf46a143d31f40f0ce7bf233505fcf692b28e2654f",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-75576402e12e975be45c7df8aedc68ee1d65a2991153409c6ff0b2eda5707bcd",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.9015625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 63,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 51,
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
        "correct": 57,
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
    "primary_joint": 0.765625,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第35轮

**当时目的与操作理由（原文）**

Round 35 of 50: restore bigger-to-larger alpha 0.5 and reduce normally-to-typically to alpha 0.25; pictured-to-image and -world-to-world remain 0.5. Preserve the round 30 visual and decoder norm settings. Tests whether weaker real-world-scope lexical alignment reduces control regressions while retaining counterfactual-usual gains.

**本轮原记录的主分数**：`0.68359375`；保留原始0–1尺度。

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
  "changed_scalars": 35794,
  "id": "c-871ab6e0f8a46030f2b40a77399fd0390987096c714ef1424aa7904b47c73ae4",
  "l2": 12.857059220368468,
  "parent": "c-75576402e12e975be45c7df8aedc68ee1d65a2991153409c6ff0b2eda5707bcd",
  "rationale": "Round 35 of 50: restore bigger-to-larger alpha 0.5 and reduce normally-to-typically to alpha 0.25; pictured-to-image and -world-to-world remain 0.5. Preserve the round 30 visual and decoder norm settings. Tests whether weaker real-world-scope lexical alignment reduces control regressions while retaining counterfactual-usual gains.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10194,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "e171371bfe62eb4a6961ca2c560b4f728cca3298295aa59098606339f1cbb067",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-871ab6e0f8a46030f2b40a77399fd0390987096c714ef1424aa7904b47c73ae4",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.899609375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
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
        "correct": 45,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 57,
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
    "repair_score": 0.68359375,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第36轮

**当时目的与操作理由（原文）**

Round 36 of 50: set the norm-preserving normally-to-typically mixture to alpha 0.75; pictured-to-image, bigger-to-larger, and -world-to-world remain 0.5. Retain all round 30 nonembedding settings. Complements round 35's alpha 0.25 test, which reduced B0 joint correctness despite repairing two answers relative to round 30.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T1:1:original_usual"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 35811,
  "id": "c-83515549cdee0babb90dd8dcb9ea1fdf374e2ae80f5547754588915816ad07ab",
  "l2": 12.88577210880528,
  "parent": "c-871ab6e0f8a46030f2b40a77399fd0390987096c714ef1424aa7904b47c73ae4",
  "rationale": "Round 36 of 50: set the norm-preserving normally-to-typically mixture to alpha 0.75; pictured-to-image, bigger-to-larger, and -world-to-world remain 0.5. Retain all round 30 nonembedding settings. Complements round 35's alpha 0.25 test, which reduced B0 joint correctness despite repairing two answers relative to round 30.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10211,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "91408541a1d970fb06749d9b64b4acee97a37d998580f2e5061e9323d306b18f",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-83515549cdee0babb90dd8dcb9ea1fdf374e2ae80f5547754588915816ad07ab",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.901953125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 61,
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
        "correct": 50,
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
        "correct": 57,
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
    "primary_joint": 0.765625,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第37轮

**当时目的与操作理由（原文）**

Round 37 of 50: set the norm-preserving -world-to-world mixture to alpha 0.25 and restore normally-to-typically to 0.5; pictured-to-image and bigger-to-larger remain 0.5. Preserve all round 30 nonembedding settings. Tests weaker scope-token alignment independently; round 36's stronger normally mixture was ineligible because a protected original-usual cell dropped 3/64 versus W0.

**本轮原记录的主分数**：`0.70703125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-3405953349ad6ffe7f31c8c46de76852eeae049d818de3437e7d161d045c30e4",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.70703125
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 35792,
  "id": "c-3405953349ad6ffe7f31c8c46de76852eeae049d818de3437e7d161d045c30e4",
  "l2": 12.861989919137924,
  "parent": "c-83515549cdee0babb90dd8dcb9ea1fdf374e2ae80f5547754588915816ad07ab",
  "rationale": "Round 37 of 50: set the norm-preserving -world-to-world mixture to alpha 0.25 and restore normally-to-typically to 0.5; pictured-to-image and bigger-to-larger remain 0.5. Preserve all round 30 nonembedding settings. Tests weaker scope-token alignment independently; round 36's stronger normally mixture was ineligible because a protected original-usual cell dropped 3/64 versus W0.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-3405953349ad6ffe7f31c8c46de76852eeae049d818de3437e7d161d045c30e4",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.90234375,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 55,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 57,
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
    "primary_joint": 0.765625,
    "repair_score": 0.70703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第38轮

**当时目的与操作理由（原文）**

Round 38 of 50: set the norm-preserving -world-to-world mixture to alpha 0.75; the other three lexical mixtures remain 0.5 and all nonembedding weights retain round 30 settings. Completes the opposing-strength test after alpha 0.25 improved B0 joint correctness to 181/256 with two repairs and no correctness regressions relative to round 30.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

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
  "changed_scalars": 35813,
  "id": "c-8c91216902f89977fcf5d2a66a00c78f89467c8dc3832c4b8f9b75d0de22601d",
  "l2": 12.877694006624019,
  "parent": "c-3405953349ad6ffe7f31c8c46de76852eeae049d818de3437e7d161d045c30e4",
  "rationale": "Round 38 of 50: set the norm-preserving -world-to-world mixture to alpha 0.75; the other three lexical mixtures remain 0.5 and all nonembedding weights retain round 30 settings. Completes the opposing-strength test after alpha 0.25 improved B0 joint correctness to 181/256 with two repairs and no correctness regressions relative to round 30.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10213,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "be1802f135036443046486316283cabb96149860b6d8e3af916d7b90262696a3",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-8c91216902f89977fcf5d2a66a00c78f89467c8dc3832c4b8f9b75d0de22601d",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.900390625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 47,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 56,
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
    "primary_joint": 0.765625,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第39轮

**当时目的与操作理由（原文）**

Round 39 of 50: restore the -world embedding row to W0 (mixture alpha 0), retaining alpha 0.5 for pictured-to-image, bigger-to-larger, and normally-to-typically. Keep all round 30 nonembedding settings. Tests whether removing this edit preserves or improves round 37's gains; alpha 0.75 underperformed alpha 0.25 and introduced no-image regressions.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

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
  "changed_scalars": 33257,
  "id": "c-2d289380b54983d901efb30470d4bcbf16f49510bf587fafc9ae0a9781fc45de",
  "l2": 12.86022862602317,
  "parent": "c-8c91216902f89977fcf5d2a66a00c78f89467c8dc3832c4b8f9b75d0de22601d",
  "rationale": "Round 39 of 50: restore the -world embedding row to W0 (mixture alpha 0), retaining alpha 0.5 for pictured-to-image, bigger-to-larger, and normally-to-typically. Keep all round 30 nonembedding settings. Tests whether removing this edit preserves or improves round 37's gains; alpha 0.75 underperformed alpha 0.25 and introduced no-image regressions.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 7657,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "b429326d883d2fabcea727371d3bf8f7e04771929d225fa3e304aabe6a03904d",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-2d289380b54983d901efb30470d4bcbf16f49510bf587fafc9ae0a9781fc45de",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.9015625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 40,
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
        "correct": 51,
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
        "correct": 56,
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
    "primary_joint": 0.765625,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第40轮

**当时目的与操作理由（原文）**

Round 40 of 50: set -world-to-world norm-preserving mixture alpha to 0.125, midway between ablation and round 37's 0.25. Keep the other lexical mixtures at 0.5 and all round 30 nonembedding settings unchanged. Tests whether a smaller scope-token edit preserves the joint-pair and no-image gains lost by complete ablation.

**本轮原记录的主分数**：`0.70703125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T1:1:original_usual"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 35766,
  "id": "c-c653fd82a9cac4d9b6dc65777deffba0109e43bf29734516cbd730a08f8147e8",
  "l2": 12.860640553767274,
  "parent": "c-2d289380b54983d901efb30470d4bcbf16f49510bf587fafc9ae0a9781fc45de",
  "rationale": "Round 40 of 50: set -world-to-world norm-preserving mixture alpha to 0.125, midway between ablation and round 37's 0.25. Keep the other lexical mixtures at 0.5 and all round 30 nonembedding settings unchanged. Tests whether a smaller scope-token edit preserves the joint-pair and no-image gains lost by complete ablation.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10166,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "73e34d19bd39fecb0fc2ff208e1a86a313c630f6bf3d53fb7e2dfebf47d6991d",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-c653fd82a9cac4d9b6dc65777deffba0109e43bf29734516cbd730a08f8147e8",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.90078125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 55,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 61,
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
        "correct": 50,
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
        "correct": 56,
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
    "repair_score": 0.70703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第41轮

**当时目的与操作理由（原文）**

Round 41 of 50: use round 37 lexical mixtures (-world alpha 0.25; other three alpha 0.5) and reduce the main visual merger norm weight and bias to 0.75 times W0 instead of 0.85. Keep deepstack merger 2 norm gain 1.15 and decoder layers 18-23 input-norm gain 1.05. Tests whether stronger main-path attenuation improves scope-sensitive joint correctness without violating controls.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

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
  "changed_scalars": 35792,
  "id": "c-f7b13719a3bacb47a98093e910abcf64b44a6587ac5bc8f98aea57efafa0f3e6",
  "l2": 15.564161627754116,
  "parent": "c-c653fd82a9cac4d9b6dc65777deffba0109e43bf29734516cbd730a08f8147e8",
  "rationale": "Round 41 of 50: use round 37 lexical mixtures (-world alpha 0.25; other three alpha 0.5) and reduce the main visual merger norm weight and bias to 0.75 times W0 instead of 0.85. Keep deepstack merger 2 norm gain 1.15 and decoder layers 18-23 input-norm gain 1.05. Tests whether stronger main-path attenuation improves scope-sensitive joint correctness without violating controls.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "7b7eaac17d5e137c2263edb0edc6e449e0a67805f717a04caf241fa5e0dcb7a0",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "b7c75cfead248efe52b014d1c4f68c617fb426450f97a21592c0e3ec63b8aacd",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f7b13719a3bacb47a98093e910abcf64b44a6587ac5bc8f98aea57efafa0f3e6",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.9015625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 54,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 61,
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
        "correct": 55,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 55,
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
    "primary_joint": 0.765625,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第42轮

**当时目的与操作理由（原文）**

Round 42 of 50: set main visual merger norm weight and bias to 0.95 times W0, keeping deepstack merger 2 at 1.15, decoder layers 18-23 input norms at 1.05, and round 37 lexical mixtures. Complements the 0.75 main-gain probe, which lost one B0 joint-correct pair relative to round 37 while leaving no-image outputs unchanged.

**本轮原记录的主分数**：`0.6953125`；保留原始0–1尺度。

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
  "changed_scalars": 35792,
  "id": "c-8427b9fc94ae1c1cf55498f643fb2a6ef826653e922c3fc651e98b143a2e4e7d",
  "l2": 11.267873911280399,
  "parent": "c-f7b13719a3bacb47a98093e910abcf64b44a6587ac5bc8f98aea57efafa0f3e6",
  "rationale": "Round 42 of 50: set main visual merger norm weight and bias to 0.95 times W0, keeping deepstack merger 2 at 1.15, decoder layers 18-23 input norms at 1.05, and round 37 lexical mixtures. Complements the 0.75 main-gain probe, which lost one B0 joint-correct pair relative to round 37 while leaving no-image outputs unchanged.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "e57b21ae9422904abafd34e3c5421485c6e1ece2cdf959bb3fb744dcf82a177a",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "904bbd45b8d4ae534880c516ecba49984c1dd94b1c0ed44dee0188af30485ca4",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-8427b9fc94ae1c1cf55498f643fb2a6ef826653e922c3fc651e98b143a2e4e7d",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.9,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 36,
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
        "correct": 51,
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
        "correct": 57,
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
    "primary_joint": 0.75,
    "repair_score": 0.6953125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第43轮

**当时目的与操作理由（原文）**

Round 43 of 50: restore main visual merger norm weight and bias to 0.85 times W0 and reduce deepstack merger 2 norm weight and bias to 1.05 times W0. Retain round 37 lexical mixtures and decoder layers 18-23 input-norm gain 1.05. Isolates weaker deepstack amplification against round 37 after main gains 0.75 and 0.95 both reduced B0 joint correctness.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

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
  "changed_scalars": 35792,
  "id": "c-2dbd79bfc7aa6c1ff62a086181c73ec9856b015bcc540395355be4cd5ab0c7b6",
  "l2": 8.97531797352459,
  "parent": "c-8427b9fc94ae1c1cf55498f643fb2a6ef826653e922c3fc651e98b143a2e4e7d",
  "rationale": "Round 43 of 50: restore main visual merger norm weight and bias to 0.85 times W0 and reduce deepstack merger 2 norm weight and bias to 1.05 times W0. Retain round 37 lexical mixtures and decoder layers 18-23 input-norm gain 1.05. Isolates weaker deepstack amplification against round 37 after main gains 0.75 and 0.95 both reduced B0 joint correctness.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "103fee4ca175a4187356637a12f69956f8533bdf89b5be656239eba5459e1f85",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "2666e4a07234e5a090b5a63837c4bf10d82ec2ac5e55c91d59ab5c40d3aa7e61",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-2dbd79bfc7aa6c1ff62a086181c73ec9856b015bcc540395355be4cd5ab0c7b6",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.901953125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 55,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 51,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 55,
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
    "primary_joint": 0.765625,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第44轮

**当时目的与操作理由（原文）**

Round 44 of 50: increase deepstack merger 2 norm weight and bias to 1.25 times W0, keeping main merger gain 0.85, round 37 lexical mixtures, and decoder layers 18-23 input-norm gain 1.05. Complements the 1.05 deepstack probe, which reduced baseline regressions but scored 180/256 B0 joint-correct pairs versus round 37's 181/256.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

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
  "changed_scalars": 35792,
  "id": "c-e29eb200daedfc8b3fdad26da4726c18bd9168bedea3556892b4ac5766ad3b24",
  "l2": 18.275228486698666,
  "parent": "c-2dbd79bfc7aa6c1ff62a086181c73ec9856b015bcc540395355be4cd5ab0c7b6",
  "rationale": "Round 44 of 50: increase deepstack merger 2 norm weight and bias to 1.25 times W0, keeping main merger gain 0.85, round 37 lexical mixtures, and decoder layers 18-23 input-norm gain 1.05. Complements the 1.05 deepstack probe, which reduced baseline regressions but scored 180/256 B0 joint-correct pairs versus round 37's 181/256.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c36d3abe2bdf79fcca0933c3d5988616026f96392001ac7cb15e82c793db1fa1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "698e5b8f89447f201fd46c40135743045251c41995185a435fed350999b21998",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "11b7aa68fd8b01cf85d05446b9ff2c383ab09780a4aed6382356c1f3610c4b5b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "7d96dfc230af98718f5461491189045a0b69c891f0f4cc0779030780dc3a13f3",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "35b92570563ed400153120027167bfde1d12e705962eb0ada4c890fad334b505",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "dff61e90e30c5b3a6a4fe2e6cc2e10616de0ed2e07db3d53431a0614a8d3363a",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "eff553858ae15e4308e12d85ff473257bf795d79302e4d67d0d12e5924eb1870",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "90aa4ec57157423099880d314f243247c28a4f217a10b32e72a96b23a7f2c730",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-e29eb200daedfc8b3fdad26da4726c18bd9168bedea3556892b4ac5766ad3b24",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.901953125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 51,
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
        "correct": 57,
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
    "primary_joint": 0.734375,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第45轮

**当时目的与操作理由（原文）**

Round 45 of 50: restore main/deepstack-2 visual norm gains to 0.85/1.15 and reduce decoder layers 18-23 input-norm gain from 1.05 to 1.025, all relative to W0. Retain round 37 lexical mixtures. Tests whether a smaller decoder edit preserves joint correctness while reducing collateral changes; both neighboring deepstack gains scored below round 37.

**本轮原记录的主分数**：`0.70703125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-556e560bdc90cca68fd2622fa57651d2e7fc071f2dd83d39ea866c91f3b393f0",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.70703125
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 35792,
  "id": "c-556e560bdc90cca68fd2622fa57651d2e7fc071f2dd83d39ea866c91f3b393f0",
  "l2": 12.102213846649134,
  "parent": "c-e29eb200daedfc8b3fdad26da4726c18bd9168bedea3556892b4ac5766ad3b24",
  "rationale": "Round 45 of 50: restore main/deepstack-2 visual norm gains to 0.85/1.15 and reduce decoder layers 18-23 input-norm gain from 1.05 to 1.025, all relative to W0. Retain round 37 lexical mixtures. Tests whether a smaller decoder edit preserves joint correctness while reducing collateral changes; both neighboring deepstack gains scored below round 37.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c353755a8c4a83ff892f778bdc5f7c99e6c7cefe3b284fe8d5a412588112d19c",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "b3a6620616cc4301b1a8e8b0df98744217a8ecac1f5791a74848fa1892d42292",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "53ab3aa0f3db835fc9405f2cfc6b262ba6a071f6b6563bddd9ad8395aadb9d93",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "a56e1bf635ec53215780a1006952aed23d98f2105de3f39ef8c4e27006f1486e",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "aca6273c5c42b3f96ac033e916c03ad8844ffec7097312c77aa6c59a79fdf504",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "d08d074a54cbabc90815eaa80b8cbc9cc293492fc2e4cae06beffc9751c147b4",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-556e560bdc90cca68fd2622fa57651d2e7fc071f2dd83d39ea866c91f3b393f0",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.901953125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 55,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 56,
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
    "primary_joint": 0.765625,
    "repair_score": 0.70703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第46轮

**当时目的与操作理由（原文）**

Round 46 of 50: restore decoder layers 18-23 input-layernorm weights exactly to W0, retaining round 37 lexical mixtures and main/deepstack-2 visual norm gains 0.85/1.15. This ablation tests whether the decoder edit is necessary after lexical refinement; gain 1.025 tied round 37's 181/256 B0 joint score but lost one B1 counterfactual-visual answer.

**本轮原记录的主分数**：`0.69921875`；保留原始0–1尺度。

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
  "changed_scalars": 20432,
  "id": "c-2465103b89537f25236cbd7bd7f056b52ad9ffe2794b3db9883beffb99887aee",
  "l2": 11.836744772259365,
  "parent": "c-556e560bdc90cca68fd2622fa57651d2e7fc071f2dd83d39ea866c91f3b393f0",
  "rationale": "Round 46 of 50: restore decoder layers 18-23 input-layernorm weights exactly to W0, retaining round 37 lexical mixtures and main/deepstack-2 visual norm gains 0.85/1.15. This ablation tests whether the decoder edit is necessary after lexical refinement; gain 1.025 tied round 37's 181/256 B0 joint score but lost one B1 counterfactual-visual answer.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-2465103b89537f25236cbd7bd7f056b52ad9ffe2794b3db9883beffb99887aee",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.9015625,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 39,
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
        "correct": 50,
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
        "correct": 57,
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
    "primary_joint": 0.75,
    "repair_score": 0.69921875,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第47轮

**当时目的与操作理由（原文）**

Round 47 of 50: scale decoder layers 18-20 input-layernorm weights to 1.025 times W0, leaving layers 21-23 at W0. Retain round 37 lexical mixtures and main/deepstack-2 visual norm gains 0.85/1.15. Tests whether the first half of the decoder band recovers the two B0 joint-correct pairs lost by complete decoder ablation, using fewer changed scalars than round 45.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

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
  "changed_scalars": 28112,
  "id": "c-9fdd7e6b3351e5b440acdad66ca36e2d7320f182579690ffedfca18071414541",
  "l2": 11.934345162082781,
  "parent": "c-2465103b89537f25236cbd7bd7f056b52ad9ffe2794b3db9883beffb99887aee",
  "rationale": "Round 47 of 50: scale decoder layers 18-20 input-layernorm weights to 1.025 times W0, leaving layers 21-23 at W0. Retain round 37 lexical mixtures and main/deepstack-2 visual norm gains 0.85/1.15. Tests whether the first half of the decoder band recovers the two B0 joint-correct pairs lost by complete decoder ablation, using fewer changed scalars than round 45.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c353755a8c4a83ff892f778bdc5f7c99e6c7cefe3b284fe8d5a412588112d19c",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "b3a6620616cc4301b1a8e8b0df98744217a8ecac1f5791a74848fa1892d42292",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "53ab3aa0f3db835fc9405f2cfc6b262ba6a071f6b6563bddd9ad8395aadb9d93",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-9fdd7e6b3351e5b440acdad66ca36e2d7320f182579690ffedfca18071414541",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.90078125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 50,
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
        "correct": 55,
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
    "primary_joint": 0.765625,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第48轮

**当时目的与操作理由（原文）**

Round 48 of 50: restore decoder layers 18-20 input-layernorm weights to W0 and scale layers 21-23 to 1.025 times W0. Retain round 37 lexical mixtures and main/deepstack-2 visual norm gains 0.85/1.15. Complements round 47's first-half probe, which recovered one B0 joint-correct pair over complete decoder ablation but remained one pair below round 45.

**本轮原记录的主分数**：`0.6953125`；保留原始0–1尺度。

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
  "changed_scalars": 28112,
  "id": "c-e2b9250cd1f1321dfa6fbaef1c6612b15c87dffb7b82542d05c837a97836cac3",
  "l2": 12.005978191963651,
  "parent": "c-9fdd7e6b3351e5b440acdad66ca36e2d7320f182579690ffedfca18071414541",
  "rationale": "Round 48 of 50: restore decoder layers 18-20 input-layernorm weights to W0 and scale layers 21-23 to 1.025 times W0. Retain round 37 lexical mixtures and main/deepstack-2 visual norm gains 0.85/1.15. Complements round 47's first-half probe, which recovered one B0 joint-correct pair over complete decoder ablation but remained one pair below round 45.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "a56e1bf635ec53215780a1006952aed23d98f2105de3f39ef8c4e27006f1486e",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "aca6273c5c42b3f96ac033e916c03ad8844ffec7097312c77aa6c59a79fdf504",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "d08d074a54cbabc90815eaa80b8cbc9cc293492fc2e4cae06beffc9751c147b4",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-e2b9250cd1f1321dfa6fbaef1c6612b15c87dffb7b82542d05c837a97836cac3",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.901171875,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 40,
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
        "correct": 50,
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
        "correct": 56,
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
    "primary_joint": 0.734375,
    "repair_score": 0.6953125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第49轮

**当时目的与操作理由（原文）**

Round 49 of 50: restore decoder layers 18-23 input-layernorm weights to 1.025 times W0 and additionally scale layers 30-35 input-layernorm weights to 1.1 times W0. Retain round 37 lexical mixtures and main/deepstack-2 visual norm gains 0.85/1.15. Both half-band probes scored below round 45. This tests whether the late-layer edit previously associated with higher overall accuracy adds useful gains to the selected full-band configuration without violating protected cells.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

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
  "changed_scalars": 51152,
  "id": "c-0ddd8f8a20b458cbaa3c7e11e30c4a45b94e72507a8466d84a739ef3a2008799",
  "l2": 47.724090485692436,
  "parent": "c-e2b9250cd1f1321dfa6fbaef1c6612b15c87dffb7b82542d05c837a97836cac3",
  "rationale": "Round 49 of 50: restore decoder layers 18-23 input-layernorm weights to 1.025 times W0 and additionally scale layers 30-35 input-layernorm weights to 1.1 times W0. Retain round 37 lexical mixtures and main/deepstack-2 visual norm gains 0.85/1.15. Both half-band probes scored below round 45. This tests whether the late-layer edit previously associated with higher overall accuracy adds useful gains to the selected full-band configuration without violating protected cells.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c353755a8c4a83ff892f778bdc5f7c99e6c7cefe3b284fe8d5a412588112d19c",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "b3a6620616cc4301b1a8e8b0df98744217a8ecac1f5791a74848fa1892d42292",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "53ab3aa0f3db835fc9405f2cfc6b262ba6a071f6b6563bddd9ad8395aadb9d93",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "a56e1bf635ec53215780a1006952aed23d98f2105de3f39ef8c4e27006f1486e",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "aca6273c5c42b3f96ac033e916c03ad8844ffec7097312c77aa6c59a79fdf504",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "d08d074a54cbabc90815eaa80b8cbc9cc293492fc2e4cae06beffc9751c147b4",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.30.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "8a3aaeef9a9cbbe5940270bbb9121ff794bf62a2e95ad636d84a1faea80dfa13.npy",
      "sha256": "a38948445d9408fc445586e7b935869c804fcd6bbd5cd8f6d378e0506919b5b9",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.31.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f22ed3e0610b87f05c103e551e925c979d409b3c12d24a82b99aef5e28441bf6.npy",
      "sha256": "2d1078f6ef58185e9cdd80a7a4da96f8f65e14f318c7fa365ff4b843ea5b460a",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.32.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "423da1a777e819de9f2787aa3fb1264904059a69f2a11a4c04a9c1656a296397.npy",
      "sha256": "8e32069610871bdbaa8678dbb3486c2286dadd9bdd4820b14b3d7ceb9be033cb",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.33.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9097eac7d3276829df5def659aca29ed0a97b4370f5cc86ae93ce0875c89b002.npy",
      "sha256": "991388d8626926bf706823dbe310f195bd404ed7f4c982dbd29ad91f3e9adf8f",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.34.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "4b3c31b7ed083725bcbf2b081923f6c2cf83690bbc897c72e70754ac1d2acb05.npy",
      "sha256": "96ed212983703026cadeaaeeb8c093a13d3770a409df0ec2d48cc7f8ad928860",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.35.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9e354f42aa507c300b7e80d2c41384682ac4ecb666f0aecdac7e0d870b295c94.npy",
      "sha256": "2d79098983c5ab61b1c34985780f65cbda2d3d5f67fed3fa51de3cfd4f72bd27",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "0ab41020dedafea897b13fe1b3b2a6006acf75e37590c985b90b5d79e32ae6ab",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "a065c9c355459edc6a0c417574a70217b46bd415e47ea68eaf2251a1b1954528",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-0ddd8f8a20b458cbaa3c7e11e30c4a45b94e72507a8466d84a739ef3a2008799",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.90078125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 55,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 48,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 62,
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
        "correct": 55,
        "n": 64
      },
      "B1:T1:0:counterfact_visual": {
        "correct": 50,
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
        "correct": 56,
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
    "primary_joint": 0.75,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

## 第50轮

**当时目的与操作理由（原文）**

Round 50 of 50: restore decoder layers 30-35 input-layernorm weights exactly to W0 and set main visual merger norm weight and bias to 0.80 times W0. Retain decoder layers 18-23 input-norm gain 1.025, deepstack merger 2 norm gain 1.15, and round 37 lexical mixtures. Round 49 added no correct answers and caused three regressions versus round 45. This final probe refines main-path attenuation between the previously tested 0.75 and 0.85 gains; relative to round 45, only the main-merger gain differs.

**本轮原记录的主分数**：`0.703125`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T1:1:original_usual"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 35792,
  "id": "c-cb559d5f6308dc20cad4f5bd718a672d296b96914616489b469135be9d5995e2",
  "l2": 13.416886855439616,
  "parent": "c-0ddd8f8a20b458cbaa3c7e11e30c4a45b94e72507a8466d84a739ef3a2008799",
  "rationale": "Round 50 of 50: restore decoder layers 30-35 input-layernorm weights exactly to W0 and set main visual merger norm weight and bias to 0.80 times W0. Retain decoder layers 18-23 input-norm gain 1.025, deepstack merger 2 norm gain 1.15, and round 37 lexical mixtures. Round 49 added no correct answers and caused three regressions versus round 45. This final probe refines main-path attenuation between the previously tested 0.75 and 0.85 gains; relative to round 45, only the main-merger gain differs.",
  "tensors": {
    "model.language_model.embed_tokens.weight": {
      "changed": 10192,
      "dtype": "BF16",
      "file": "4686a87132df8c87401f0cccfa790a2e5108989cf3cf51c195b77d345c252fee.npy",
      "sha256": "4faee1a77bcc360cdf5568f9c1573fcab29e708b8dfe9552e919029507d41f81",
      "shape": [
        151936,
        2560
      ]
    },
    "model.language_model.layers.18.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f70fffc080783a9e956ff054795084a02229b60a854a1c55c6685a413e14f31f.npy",
      "sha256": "c353755a8c4a83ff892f778bdc5f7c99e6c7cefe3b284fe8d5a412588112d19c",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.19.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ad735dceb834e9aa8bbc533792510b3bd3030cc712aa47c2ee8c2e8baa1a9752.npy",
      "sha256": "b3a6620616cc4301b1a8e8b0df98744217a8ecac1f5791a74848fa1892d42292",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.20.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "edf3cc44bff8a6a70d1fc8061f060950671582bfc0d9590276183d20d54c7bcd.npy",
      "sha256": "53ab3aa0f3db835fc9405f2cfc6b262ba6a071f6b6563bddd9ad8395aadb9d93",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.21.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bdfc5caf464c75b12a8003673c2c62a789525dae8e648fd792dda306eda81e4c.npy",
      "sha256": "a56e1bf635ec53215780a1006952aed23d98f2105de3f39ef8c4e27006f1486e",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.22.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b32b36b3b7ce0458119ea8f3e700c3b64fdf6c94038f59526c3ed0635186a4b0.npy",
      "sha256": "aca6273c5c42b3f96ac033e916c03ad8844ffec7097312c77aa6c59a79fdf504",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.23.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d59603fad95df2cd22f504077368efaea1e88848050ee33adaaaf60ee3c7a80d.npy",
      "sha256": "d08d074a54cbabc90815eaa80b8cbc9cc293492fc2e4cae06beffc9751c147b4",
      "shape": [
        2560
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "53b0fa93965743180aec5194637a173f4d8844edb5f75e18af2c3abc052ea39c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "32eb0cf0bc08a3cb0b6edb048b741a00c669ae210b5e08da55feffd0d3006aab",
      "shape": [
        4096
      ]
    },
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "9dc8975b690385928818bd0676449fb295f297ab27e65f1e58c6de6b94ad91e6",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "bfc03da37bcfa14c5ac4cf19a4badd29dd2deda7e22b7349d171c7e8e035ffbb",
      "shape": [
        1024
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-cb559d5f6308dc20cad4f5bd718a672d296b96914616489b469135be9d5995e2",
  "full_development": true,
  "protocol": "81edb63fca657a7103b4e7a2b4b3211bf279120939467432e889e5455cb28ece",
  "summary": {
    "accuracy": 0.901953125,
    "cells": {
      "B0:T0:0:counterfact_usual": {
        "correct": 53,
        "n": 64
      },
      "B0:T0:0:counterfact_visual": {
        "correct": 62,
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
        "correct": 54,
        "n": 64
      },
      "B0:T1:0:counterfact_visual": {
        "correct": 53,
        "n": 64
      },
      "B0:T1:0:no_image_usual": {
        "correct": 60,
        "n": 64
      },
      "B0:T1:0:original_usual": {
        "correct": 62,
        "n": 64
      },
      "B0:T1:0:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B0:T1:1:counterfact_usual": {
        "correct": 50,
        "n": 64
      },
      "B0:T1:1:counterfact_visual": {
        "correct": 52,
        "n": 64
      },
      "B0:T1:1:no_image_usual": {
        "correct": 49,
        "n": 64
      },
      "B0:T1:1:original_usual": {
        "correct": 61,
        "n": 64
      },
      "B0:T1:1:original_visual": {
        "correct": 64,
        "n": 64
      },
      "B1:T0:0:counterfact_usual": {
        "correct": 53,
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
        "correct": 39,
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
        "correct": 50,
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
        "correct": 55,
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
    "primary_joint": 0.75,
    "repair_score": 0.703125,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 2560, "predictions": 2560, "scored": 2560}`。

