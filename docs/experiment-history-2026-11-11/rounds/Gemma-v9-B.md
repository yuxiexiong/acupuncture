# Gemma-v9-B：逐轮目的、修改与结果

本页逐轮转录已归档值，不重新评分、不运行模型。共30个完整候选；不是新增30次实验。研究者当时的理由按原文保留，其中预期不能读作已验证结果。每轮均从其记录指定的基线和父候选解释，不能默认累加补丁。

原始完整档案（含逐题答案）：

- [experiments/wsp-vlm-gemma3-v9-shared-admission-2026-11-06/resume-final-audit/B-remote-evidence.tar.gz.part000](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-v9-shared-admission-2026-11-06/resume-final-audit/B-remote-evidence.tar.gz.part000)

## 第1轮

**当时目的与操作理由（原文）**

Round 1: test whether suppressing opposing MLP writes at the strongest cross-source residual-localization site reduces instruction-sensitive spatial overcounting. No claim of a universal spatial or zero-count mechanism.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 315332,
  "id": "c-c4ec1a6a917668e504b846cbd91c589138fb843d1f2c1e9a9048d6b2e6a9f2cb",
  "l2": 0.1847874701039664,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Round 1: test whether suppressing opposing MLP writes at the strongest cross-source residual-localization site reduces instruction-sensitive spatial overcounting. No claim of a universal spatial or zero-count mechanism.",
  "tensors": {
    "language_model.model.layers.15.mlp.down_proj.weight": {
      "base_sha256": "5c91b7ffbc2caefbf4ee8c663b969c84bd6612bce6b71bade5326ef6cfcb7658",
      "changed": 315332,
      "content_sha256": "a27ccdf1ede1e7e6cb8b334afa0b7d434cf07f5dde2446787249d9fd059a084b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d1c22bc5b4c5e89e96731058caaebd81a03e061022317d0081526d04793e9c0f.npz",
      "sha256": "9d28a553686ab8645b1fdabcc001898c188ba689d2ac84b570ee2f02e5172891",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 315332
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-c4ec1a6a917668e504b846cbd91c589138fb843d1f2c1e9a9048d6b2e6a9f2cb",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4375,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 3
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第2轮

**当时目的与操作理由（原文）**

Round 2: strong-dose falsification of layer-15 opposing-write hypothesis after round 1 produced two repairs, one loss, and a worse joint endpoint.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 323625,
  "id": "c-ca1fd32687347ea8afbfe384a32eca2c5f090a3a341c7b73dcee390bbe863ad5",
  "l2": 0.5542326181252037,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Round 2: strong-dose falsification of layer-15 opposing-write hypothesis after round 1 produced two repairs, one loss, and a worse joint endpoint.",
  "tensors": {
    "language_model.model.layers.15.mlp.down_proj.weight": {
      "base_sha256": "5c91b7ffbc2caefbf4ee8c663b969c84bd6612bce6b71bade5326ef6cfcb7658",
      "changed": 323625,
      "content_sha256": "655626fd7829bededed52894d52b82f72797e4053a8749e4c5f8a0c40ee30711",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d1c22bc5b4c5e89e96731058caaebd81a03e061022317d0081526d04793e9c0f.npz",
      "sha256": "64be0ad2ea5a5d93b3f3fb3662ac2f3ef38aac2dfac2180b347716f0db24ca8f",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 323625
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-ca1fd32687347ea8afbfe384a32eca2c5f090a3a341c7b73dcee390bbe863ad5",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4331896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 33,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 2,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第3轮

**当时目的与操作理由（原文）**

Round 3: preplanned weak-dose test. Absolute replacement of the same tensor reconstructed from W0, not cumulative editing.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 303157,
  "id": "c-56fbfac90fd712acc8d09c7b62fdef29fdc6055677815a47dbf492dc1e6673eb",
  "l2": 0.09250112627153091,
  "parent": "c-ca1fd32687347ea8afbfe384a32eca2c5f090a3a341c7b73dcee390bbe863ad5",
  "rationale": "Round 3: preplanned weak-dose test. Absolute replacement of the same tensor reconstructed from W0, not cumulative editing.",
  "tensors": {
    "language_model.model.layers.15.mlp.down_proj.weight": {
      "base_sha256": "5c91b7ffbc2caefbf4ee8c663b969c84bd6612bce6b71bade5326ef6cfcb7658",
      "changed": 303157,
      "content_sha256": "6a293931c6cda1105227fa3627d3d35f408fc9e945f14af514658267c1b05735",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d1c22bc5b4c5e89e96731058caaebd81a03e061022317d0081526d04793e9c0f.npz",
      "sha256": "71563b0711886de9e56dbf3c228927e089be7b0f6b6e37698d238acdb666cc85",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 303157
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-56fbfac90fd712acc8d09c7b62fdef29fdc6055677815a47dbf492dc1e6673eb",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4375,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第4轮

**当时目的与操作理由（原文）**

Round 4: opposite-sign causal control; same layer, channels and direction, W0-relative rather than compounded.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 315326,
  "id": "c-f424d58fbc0c68bde2d127a6fe99e7898fd822f010f788ee44f630abbad602c7",
  "l2": 0.18479350926624297,
  "parent": "c-56fbfac90fd712acc8d09c7b62fdef29fdc6055677815a47dbf492dc1e6673eb",
  "rationale": "Round 4: opposite-sign causal control; same layer, channels and direction, W0-relative rather than compounded.",
  "tensors": {
    "language_model.model.layers.15.mlp.down_proj.weight": {
      "base_sha256": "5c91b7ffbc2caefbf4ee8c663b969c84bd6612bce6b71bade5326ef6cfcb7658",
      "changed": 315326,
      "content_sha256": "8f1973f5e64e5c8e0af07f109ffd6ad4054ef5683330821b9d11211560b4360b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d1c22bc5b4c5e89e96731058caaebd81a03e061022317d0081526d04793e9c0f.npz",
      "sha256": "28badd0c5a1ddcbda557bbae616d8c1015e34735ecdf8df016235ad785e66b42",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 315326
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f424d58fbc0c68bde2d127a6fe99e7898fd822f010f788ee44f630abbad602c7",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4224137931034483,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 28,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 31,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 8,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 4
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第5轮

**当时目的与操作理由（原文）**

Round 5: direction-specificity control with fixed selected channels and fixed per-channel coefficients, replacing only the write direction by a seeded orthogonal random vector.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 315179,
  "id": "c-5f2247cf8ea2005724281021da9d14c29836ea07257fe3adf8032ec99b6e9d10",
  "l2": 0.184802047696979,
  "parent": "c-f424d58fbc0c68bde2d127a6fe99e7898fd822f010f788ee44f630abbad602c7",
  "rationale": "Round 5: direction-specificity control with fixed selected channels and fixed per-channel coefficients, replacing only the write direction by a seeded orthogonal random vector.",
  "tensors": {
    "language_model.model.layers.15.mlp.down_proj.weight": {
      "base_sha256": "5c91b7ffbc2caefbf4ee8c663b969c84bd6612bce6b71bade5326ef6cfcb7658",
      "changed": 315179,
      "content_sha256": "2b9c924f5f745391fc4b41ed59aa11c4b6a60952a7ba6c094b90dfa20896b423",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d1c22bc5b4c5e89e96731058caaebd81a03e061022317d0081526d04793e9c0f.npz",
      "sha256": "171e95562ad75aa56b7271a1d382769ba3a13c89d72bc549bbd362a8a1427d6f",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 315179
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-5f2247cf8ea2005724281021da9d14c29836ea07257fe3adf8032ec99b6e9d10",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4267241379310345,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 32,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 5,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第6轮

**当时目的与操作理由（原文）**

Round 6: test channel-selection specificity using disjoint randomized channels matched on W0 column norm and measured activation statistics; preserve direction and coefficient vector.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 315392,
  "id": "c-0901b506056bf9b33091d3b2206a26cfb82ca99bdbaa00488e1af24b5d8675c1",
  "l2": 0.18481276504673094,
  "parent": "c-5f2247cf8ea2005724281021da9d14c29836ea07257fe3adf8032ec99b6e9d10",
  "rationale": "Round 6: test channel-selection specificity using disjoint randomized channels matched on W0 column norm and measured activation statistics; preserve direction and coefficient vector.",
  "tensors": {
    "language_model.model.layers.15.mlp.down_proj.weight": {
      "base_sha256": "5c91b7ffbc2caefbf4ee8c663b969c84bd6612bce6b71bade5326ef6cfcb7658",
      "changed": 315392,
      "content_sha256": "f9fccbb48c703514a541d55d3a522ea7625a62fb736190fabd75d9e2d744900d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d1c22bc5b4c5e89e96731058caaebd81a03e061022317d0081526d04793e9c0f.npz",
      "sha256": "068d7d05d45820daa1a86c1104f8d1805c238cb1c181177d225a5a64bd8fe81a",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 315392
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-0901b506056bf9b33091d3b2206a26cfb82ca99bdbaa00488e1af24b5d8675c1",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4375,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第7轮

**当时目的与操作理由（原文）**

Round 7: generic-prefix-direction control. Random-channel reassignment reproduced the selected-channel correctness flips, so channel-specific mechanism claims are rejected.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 313961,
  "id": "c-fbc0a56b556349ccbbc4882b0c14aad8e1c805310fa649829a140fbd297bf25c",
  "l2": 0.18481215937443368,
  "parent": "c-0901b506056bf9b33091d3b2206a26cfb82ca99bdbaa00488e1af24b5d8675c1",
  "rationale": "Round 7: generic-prefix-direction control. Random-channel reassignment reproduced the selected-channel correctness flips, so channel-specific mechanism claims are rejected.",
  "tensors": {
    "language_model.model.layers.15.mlp.down_proj.weight": {
      "base_sha256": "5c91b7ffbc2caefbf4ee8c663b969c84bd6612bce6b71bade5326ef6cfcb7658",
      "changed": 313961,
      "content_sha256": "1d3b484b60aea89b08e9d997904ef65a5429133a53d4c14343bcff9a98c055fc",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d1c22bc5b4c5e89e96731058caaebd81a03e061022317d0081526d04793e9c0f.npz",
      "sha256": "34172acc7eb71727718c19b2f4fcad45c74f409be5894334bf0e2aecfa600fb4",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 313961
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-fbc0a56b556349ccbbc4882b0c14aad8e1c805310fa649829a140fbd297bf25c",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.43103448275862066,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 32,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第8轮

**当时目的与操作理由（原文）**

Round 8: revised answer-balanced hypothesis. Test sparse nonuniform layer-10 post-MLP norm gains after normalized branch captures showed more consistency than raw writes.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 256,
  "id": "c-3c85a6ea55aec23ea34ea619b1e0790a00c21fdd9be133d4cde5e88e912cebae",
  "l2": 21.267054277831946,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Round 8: revised answer-balanced hypothesis. Test sparse nonuniform layer-10 post-MLP norm gains after normalized branch captures showed more consistency than raw writes.",
  "tensors": {
    "language_model.model.layers.10.post_feedforward_layernorm.weight": {
      "base_sha256": "af7761db8fb6d65d7a92deced7aa6ed9ab39d59ee3f31efbf19eff7359129043",
      "changed": 256,
      "content_sha256": "64a617ffd66f53359226b04b5e7d859979947239c2f317aaeed9c5d237af2e73",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "72f7688908dd4021f31f16b0ab7bcd5e283e44fbb3079a8c543be98fec663b29.npz",
      "sha256": "a5c6c2e57462037826cc4ec2650963b3d1d1a609360c1843319165ac5c2241bd",
      "shape": [
        2560
      ],
      "stored_coordinates": 256
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-3c85a6ea55aec23ea34ea619b1e0790a00c21fdd9be133d4cde5e88e912cebae",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.42887931034482757,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 39,
        "n": 58
      }
    },
    "format_errors": 5,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 3
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第9轮

**当时目的与操作理由（原文）**

Round 9: quarter-dose test of the fixed sparse layer-10 norm-gain fit, reconstructed from W0 rather than compounded.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 253,
  "id": "c-6fcbd979adeff148dc4524a26d079168de8a8a8e1c2148d6d39510b0063eeb53",
  "l2": 5.591960258375412,
  "parent": "c-3c85a6ea55aec23ea34ea619b1e0790a00c21fdd9be133d4cde5e88e912cebae",
  "rationale": "Round 9: quarter-dose test of the fixed sparse layer-10 norm-gain fit, reconstructed from W0 rather than compounded.",
  "tensors": {
    "language_model.model.layers.10.post_feedforward_layernorm.weight": {
      "base_sha256": "af7761db8fb6d65d7a92deced7aa6ed9ab39d59ee3f31efbf19eff7359129043",
      "changed": 253,
      "content_sha256": "2f5e3b40410b300ca8e31676ba0a70193678359db42b5a5753a0929ba5603399",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "72f7688908dd4021f31f16b0ab7bcd5e283e44fbb3079a8c543be98fec663b29.npz",
      "sha256": "54e16aff849f100a44c9d7eac936317def7c253114ae607f9647d6b40a53e1a0",
      "shape": [
        2560
      ],
      "stored_coordinates": 253
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-6fcbd979adeff148dc4524a26d079168de8a8a8e1c2148d6d39510b0063eeb53",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.42887931034482757,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 33,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 39,
        "n": 58
      }
    },
    "format_errors": 5,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第10轮

**当时目的与操作理由（原文）**

Round 10: opposite-sign control for the fixed layer-10 sparse norm-gain fit; absolute W0-relative replacement.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 256,
  "id": "c-85d54d388453a734e5e30b33fe10cd900d03f858502264732c02634c75989a8a",
  "l2": 21.27719422622788,
  "parent": "c-6fcbd979adeff148dc4524a26d079168de8a8a8e1c2148d6d39510b0063eeb53",
  "rationale": "Round 10: opposite-sign control for the fixed layer-10 sparse norm-gain fit; absolute W0-relative replacement.",
  "tensors": {
    "language_model.model.layers.10.post_feedforward_layernorm.weight": {
      "base_sha256": "af7761db8fb6d65d7a92deced7aa6ed9ab39d59ee3f31efbf19eff7359129043",
      "changed": 256,
      "content_sha256": "78ff1e598270f484344c62cdeb82c097c25cd1c09ececf3c99d11adb06c2b697",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "72f7688908dd4021f31f16b0ab7bcd5e283e44fbb3079a8c543be98fec663b29.npz",
      "sha256": "8207724e4f497fbcb84a7987b1a012fe16022f77bc594705b829a407900aa191",
      "shape": [
        2560
      ],
      "stored_coordinates": 256
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-85d54d388453a734e5e30b33fe10cd900d03f858502264732c02634c75989a8a",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4224137931034483,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 28,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 32,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第11轮

**当时目的与操作理由（原文）**

Round 11: test specificity of the fitted coordinate-to-offset assignment by a fixed seeded permutation, reconstructed from W0.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 255,
  "id": "c-9a9d3fb778055472a9cb7e4ee52eb093da314dcbe2bb5d308370040fd31bea47",
  "l2": 21.474213506043125,
  "parent": "c-85d54d388453a734e5e30b33fe10cd900d03f858502264732c02634c75989a8a",
  "rationale": "Round 11: test specificity of the fitted coordinate-to-offset assignment by a fixed seeded permutation, reconstructed from W0.",
  "tensors": {
    "language_model.model.layers.10.post_feedforward_layernorm.weight": {
      "base_sha256": "af7761db8fb6d65d7a92deced7aa6ed9ab39d59ee3f31efbf19eff7359129043",
      "changed": 255,
      "content_sha256": "0b7581f8dc18cc2d857052d249b7bcf6aefbd10c32e2b2d2def8490c7c2b2189",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "72f7688908dd4021f31f16b0ab7bcd5e283e44fbb3079a8c543be98fec663b29.npz",
      "sha256": "ce7dd52e6b8c96f61a5bcfcea49e19f20ceb4e1a34e902ab4dbd0a084d8cfb5f",
      "shape": [
        2560
      ],
      "stored_coordinates": 255
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-9a9d3fb778055472a9cb7e4ee52eb093da314dcbe2bb5d308370040fd31bea47",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4353448275862069,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 28,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第12轮

**当时目的与操作理由（原文）**

Round 12: bounded context-dependent layer-10 MLP write correction using only reproduced failure/success contrasts.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 320117,
  "id": "c-c8f65464ad2c443cc3422afb83ca5fd2d80e805fbab186fe8feeb87fb1d624d8",
  "l2": 0.77918319881508,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Round 12: bounded context-dependent layer-10 MLP write correction using only reproduced failure/success contrasts.",
  "tensors": {
    "language_model.model.layers.10.mlp.down_proj.weight": {
      "base_sha256": "2d79f8adf60d2ffb66f98455b103f3718c04debc473659a45001f78bb4c20b44",
      "changed": 320117,
      "content_sha256": "749d33ce668cd86a2087c954bf5bf2320fe5c8364682e122684923c0cbe0b3a1",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d38a0fd5a0424c05e758141a67a45de0ba98438cca23030d5ef4f54800653cf6.npz",
      "sha256": "6c29cef14710ef0cad415fab19cf164086eebfce9f3c4d5252d25189169c972e",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 320117
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-c8f65464ad2c443cc3422afb83ca5fd2d80e805fbab186fe8feeb87fb1d624d8",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4267241379310345,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 33,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 39,
        "n": 58
      }
    },
    "format_errors": 5,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 3
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第13轮

**当时目的与操作理由（原文）**

Round 13: fourfold-strength test of the fixed context-dependent layer-10 MLP correction, reconstructed from W0.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 325784,
  "id": "c-da458586f51a0f64d12d3b16af1ceb493c2b468458ec7229f7b6610a8697e7ce",
  "l2": 3.1166515305393143,
  "parent": "c-c8f65464ad2c443cc3422afb83ca5fd2d80e805fbab186fe8feeb87fb1d624d8",
  "rationale": "Round 13: fourfold-strength test of the fixed context-dependent layer-10 MLP correction, reconstructed from W0.",
  "tensors": {
    "language_model.model.layers.10.mlp.down_proj.weight": {
      "base_sha256": "2d79f8adf60d2ffb66f98455b103f3718c04debc473659a45001f78bb4c20b44",
      "changed": 325784,
      "content_sha256": "a7e7a474c9ce5643bb571c411c9a0c3fba760cfc3614a3f4bd121fd3e15a0a0a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d38a0fd5a0424c05e758141a67a45de0ba98438cca23030d5ef4f54800653cf6.npz",
      "sha256": "8691445a033d05a831ea5af7553ee524ac630b9fc62f5b32fee45948cdf4db41",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 325784
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-da458586f51a0f64d12d3b16af1ceb493c2b468458ec7229f7b6610a8697e7ce",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.42887931034482757,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 3
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第14轮

**当时目的与操作理由（原文）**

Round 14: equal-strength opposite-sign control for the context-dependent layer-10 MLP patch.

**本轮原记录的主分数**：`0.1724137931034483`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 325783,
  "id": "c-2ad0f3e5c4095a1f1e84100f66b9e69cca5559ce6bf5c207799d2fd6515b6cab",
  "l2": 3.1166547163993816,
  "parent": "c-da458586f51a0f64d12d3b16af1ceb493c2b468458ec7229f7b6610a8697e7ce",
  "rationale": "Round 14: equal-strength opposite-sign control for the context-dependent layer-10 MLP patch.",
  "tensors": {
    "language_model.model.layers.10.mlp.down_proj.weight": {
      "base_sha256": "2d79f8adf60d2ffb66f98455b103f3718c04debc473659a45001f78bb4c20b44",
      "changed": 325783,
      "content_sha256": "7a4072d1e1dfc380477cd748dcdfca078171b3ef1182231100fe8a4c9a127eef",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d38a0fd5a0424c05e758141a67a45de0ba98438cca23030d5ef4f54800653cf6.npz",
      "sha256": "9e09e4946ac31bddc66fdc115afd550720172b376db312ab3e25e66b2a7707f2",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 325783
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-2ad0f3e5c4095a1f1e84100f66b9e69cca5559ce6bf5c207799d2fd6515b6cab",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4202586206896552,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 28,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 29,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 30,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 39,
        "n": 58
      }
    },
    "format_errors": 6,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.1724137931034483,
    "repair_score": 0.1724137931034483,
    "truncated": 4
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第15轮

**当时目的与操作理由（原文）**

Round 15: source-to-target permutation control for the conditional layer-10 MLP fit.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 325538,
  "id": "c-72cd35b996efdf2a869d4556d236f84681b3e06a6379d1b35073336c022af422",
  "l2": 3.116654615573034,
  "parent": "c-2ad0f3e5c4095a1f1e84100f66b9e69cca5559ce6bf5c207799d2fd6515b6cab",
  "rationale": "Round 15: source-to-target permutation control for the conditional layer-10 MLP fit.",
  "tensors": {
    "language_model.model.layers.10.mlp.down_proj.weight": {
      "base_sha256": "2d79f8adf60d2ffb66f98455b103f3718c04debc473659a45001f78bb4c20b44",
      "changed": 325538,
      "content_sha256": "6f160d23065a7a45804e8529ab552e50ee261c803f0d0cea2bfc07ea660955a5",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d38a0fd5a0424c05e758141a67a45de0ba98438cca23030d5ef4f54800653cf6.npz",
      "sha256": "fc74799e74b6efc0ede0defc0db13482a573c7271ead2d326936288badde7008",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 325538
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-72cd35b996efdf2a869d4556d236f84681b3e06a6379d1b35073336c022af422",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4331896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 28,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 28,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 32,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 3
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第16轮

**当时目的与操作理由（原文）**

Round 16: test 10% attenuation of layer-7 attention head 3 after reproduced-contrast screening.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 655360,
  "id": "c-2e8329f42f4b36320b032d66f7049211ed7cdc3f8a3fc61265500f17761080e9",
  "l2": 1.6723784999681621,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Round 16: test 10% attenuation of layer-7 attention head 3 after reproduced-contrast screening.",
  "tensors": {
    "language_model.model.layers.7.self_attn.o_proj.weight": {
      "base_sha256": "00425c6d47ec3dfb015ad177d26a1b94be12ce7675dfefc2588ae79f859de32e",
      "changed": 655360,
      "content_sha256": "19580feb7cb1730e28769237af7b283eb40f1a0dfa0ccbb3294541727ad85010",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "97aee9ae536d262afa8e953162e58cf011fe85d13af21e034533efa77e588e26.npz",
      "sha256": "7fe9c6177d4516f307336b4d5f9ef535ef96b8be9771922f1d6c45a73f519c8f",
      "shape": [
        2560,
        2048
      ],
      "stored_coordinates": 655360
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-2e8329f42f4b36320b032d66f7049211ed7cdc3f8a3fc61265500f17761080e9",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4267241379310345,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 32,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 7,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第17轮

**当时目的与操作理由（原文）**

Round 17: preplanned fivefold-dose test of layer-7 head-3 attenuation.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 655360,
  "id": "c-90ceb0794dc1676a002f413ab2c27befbcaa8fbd38bf3d9037f18f21c807ab17",
  "l2": 8.360465490920674,
  "parent": "c-2e8329f42f4b36320b032d66f7049211ed7cdc3f8a3fc61265500f17761080e9",
  "rationale": "Round 17: preplanned fivefold-dose test of layer-7 head-3 attenuation.",
  "tensors": {
    "language_model.model.layers.7.self_attn.o_proj.weight": {
      "base_sha256": "00425c6d47ec3dfb015ad177d26a1b94be12ce7675dfefc2588ae79f859de32e",
      "changed": 655360,
      "content_sha256": "14b4c854be15907389fd258a1073530db935602fb624d5da0154c841e8d4d96c",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "97aee9ae536d262afa8e953162e58cf011fe85d13af21e034533efa77e588e26.npz",
      "sha256": "00ac82d3b46e68ed8d2480d2b5bf66ff9369ba3f8d680234e255bd5edc440fe9",
      "shape": [
        2560,
        2048
      ],
      "stored_coordinates": 655360
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-90ceb0794dc1676a002f413ab2c27befbcaa8fbd38bf3d9037f18f21c807ab17",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4331896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 15,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 29,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 8,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 3
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第18轮

**当时目的与操作理由（原文）**

Round 18: opposite-sign control for layer-7 head-3 attenuation.

**本轮原记录的主分数**：`0.14655172413793102`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B1:T0:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 655360,
  "id": "c-4c4ef0b96c105bba4f60040bed18b13399c544879679c8c93d0969acd6c65d3a",
  "l2": 8.360256427926407,
  "parent": "c-90ceb0794dc1676a002f413ab2c27befbcaa8fbd38bf3d9037f18f21c807ab17",
  "rationale": "Round 18: opposite-sign control for layer-7 head-3 attenuation.",
  "tensors": {
    "language_model.model.layers.7.self_attn.o_proj.weight": {
      "base_sha256": "00425c6d47ec3dfb015ad177d26a1b94be12ce7675dfefc2588ae79f859de32e",
      "changed": 655360,
      "content_sha256": "592804193a3b2e3f10193a384162a2deeb94487c40248a459167458ffe812719",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "97aee9ae536d262afa8e953162e58cf011fe85d13af21e034533efa77e588e26.npz",
      "sha256": "d3e60b171c90e8ce5fe04a06c60eff2ca11b3de242d392dd94d5134e2a156688",
      "shape": [
        2560,
        2048
      ],
      "stored_coordinates": 655360
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-4c4ef0b96c105bba4f60040bed18b13399c544879679c8c93d0969acd6c65d3a",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4224137931034483,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 31,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 39,
        "n": 58
      }
    },
    "format_errors": 3,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.14655172413793102,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第19轮

**当时目的与操作理由（原文）**

Round 19: preselected, norm-matched layer-7 head-4 attenuation control.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B1:T0:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 655360,
  "id": "c-d0ea435cf315594c1edb20c55e01599264a06e3f90035a4a1e016bd110db8e79",
  "l2": 8.360875693025152,
  "parent": "c-4c4ef0b96c105bba4f60040bed18b13399c544879679c8c93d0969acd6c65d3a",
  "rationale": "Round 19: preselected, norm-matched layer-7 head-4 attenuation control.",
  "tensors": {
    "language_model.model.layers.7.self_attn.o_proj.weight": {
      "base_sha256": "00425c6d47ec3dfb015ad177d26a1b94be12ce7675dfefc2588ae79f859de32e",
      "changed": 655360,
      "content_sha256": "bd476697ffe46705d1f570afae651a3f64b1505e4dcc9e96b7a321a34f331f38",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "97aee9ae536d262afa8e953162e58cf011fe85d13af21e034533efa77e588e26.npz",
      "sha256": "a8046737a2aac1447e8569bceb922bd29bda9192734883aa73459a329b1cd7c7",
      "shape": [
        2560,
        2048
      ],
      "stored_coordinates": 655360
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-d0ea435cf315594c1edb20c55e01599264a06e3f90035a4a1e016bd110db8e79",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.42887931034482757,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 28,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 28,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 31,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 3,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第20轮

**当时目的与操作理由（原文）**

Round 20: output-coordinate permutation control for the layer-7 head-3 update.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 652919,
  "id": "c-79dba63fd2dfcf6f509b40f2b7382b2b420275690ac2615f5f39de86619c42d7",
  "l2": 8.360503128033987,
  "parent": "c-d0ea435cf315594c1edb20c55e01599264a06e3f90035a4a1e016bd110db8e79",
  "rationale": "Round 20: output-coordinate permutation control for the layer-7 head-3 update.",
  "tensors": {
    "language_model.model.layers.7.self_attn.o_proj.weight": {
      "base_sha256": "00425c6d47ec3dfb015ad177d26a1b94be12ce7675dfefc2588ae79f859de32e",
      "changed": 652919,
      "content_sha256": "d45dd994a41d91e837a5061d5662832ba9a3d34c36f6692619a5fd1eec08dd1a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "97aee9ae536d262afa8e953162e58cf011fe85d13af21e034533efa77e588e26.npz",
      "sha256": "b4d78831017ad4033682a172124635bbc0ea2472c9f927da44df04b0176cf20b",
      "shape": [
        2560,
        2048
      ],
      "stored_coordinates": 652919
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-79dba63fd2dfcf6f509b40f2b7382b2b420275690ac2615f5f39de86619c42d7",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.43103448275862066,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 33,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 41,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第21轮

**当时目的与操作理由（原文）**

Round 21: bounded, gain-aware conditional correction of the final decoder MLP write, reconstructed from W0.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 281391,
  "id": "c-50a30c46840c103d1ef66d122fd784f1526ccb3305f42c1f42603ba6dc7008c3",
  "l2": 0.8297451911826307,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Round 21: bounded, gain-aware conditional correction of the final decoder MLP write, reconstructed from W0.",
  "tensors": {
    "language_model.model.layers.33.mlp.down_proj.weight": {
      "base_sha256": "2d291bc5e5bf8a4a49641d6b3994bdcf3009ff6874a7591c6274f3ff8f302858",
      "changed": 281391,
      "content_sha256": "6bf714fe0e5d56b81676ef7fd0a4f2203bd084d0a806d1dd2860ce20e27f9b87",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "dbe9de5d5d4eb2a31b88993c18fefad68a76e2c757ab18d8c1b48566714e432f.npz",
      "sha256": "66fe59988af077c2a91330ee520a06c2a719036af744884c0cf3c5747a05fcaa",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 281391
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-50a30c46840c103d1ef66d122fd784f1526ccb3305f42c1f42603ba6dc7008c3",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4353448275862069,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第22轮

**当时目的与操作理由（原文）**

Round 22: predeclared fourfold-strength test of the fixed gain-aware layer-33 MLP correction, reconstructed from W0.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 312937,
  "id": "c-25911ce0fd2317868882852917b4bdd5007e7c6826dd4d91d048ddf4d886d8f7",
  "l2": 3.3188799173574677,
  "parent": "c-50a30c46840c103d1ef66d122fd784f1526ccb3305f42c1f42603ba6dc7008c3",
  "rationale": "Round 22: predeclared fourfold-strength test of the fixed gain-aware layer-33 MLP correction, reconstructed from W0.",
  "tensors": {
    "language_model.model.layers.33.mlp.down_proj.weight": {
      "base_sha256": "2d291bc5e5bf8a4a49641d6b3994bdcf3009ff6874a7591c6274f3ff8f302858",
      "changed": 312937,
      "content_sha256": "36e211f4041628e66ada146817cb9fd03ba48653552821779be63377cc53d100",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "dbe9de5d5d4eb2a31b88993c18fefad68a76e2c757ab18d8c1b48566714e432f.npz",
      "sha256": "ba24790dc3cd30782c0c97f6c463a3d7253920e2fb7e03023878357ed52cecd2",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 312937
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-25911ce0fd2317868882852917b4bdd5007e7c6826dd4d91d048ddf4d886d8f7",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4331896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第23轮

**当时目的与操作理由（原文）**

Round 23: predeclared equal-strength opposite-sign control for the conditional layer-33 MLP correction.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 312943,
  "id": "c-646d98308bd4c4db8500e57c0acc1593a34546691cab52f716e4c17e070c60d8",
  "l2": 3.319006193434169,
  "parent": "c-25911ce0fd2317868882852917b4bdd5007e7c6826dd4d91d048ddf4d886d8f7",
  "rationale": "Round 23: predeclared equal-strength opposite-sign control for the conditional layer-33 MLP correction.",
  "tensors": {
    "language_model.model.layers.33.mlp.down_proj.weight": {
      "base_sha256": "2d291bc5e5bf8a4a49641d6b3994bdcf3009ff6874a7591c6274f3ff8f302858",
      "changed": 312943,
      "content_sha256": "4b5e3295cab46f3b07084d4577c062d1f7e89906ede6714d08e1b4036ac14d5a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "dbe9de5d5d4eb2a31b88993c18fefad68a76e2c757ab18d8c1b48566714e432f.npz",
      "sha256": "7e69bde727aaaa93fe5d4d13fdd5aade3e3c944a08e91669f2505122eec2b4f9",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 312943
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-646d98308bd4c4db8500e57c0acc1593a34546691cab52f716e4c17e070c60d8",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4331896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第24轮

**当时目的与操作理由（原文）**

Round 24: source-to-target permutation control for the gain-aware conditional layer-33 MLP fit.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 312645,
  "id": "c-589644f45f380ff6e94113f8a53bd6f747b4ae9fd83ef493da0164ea43cff0fe",
  "l2": 3.318905031307596,
  "parent": "c-646d98308bd4c4db8500e57c0acc1593a34546691cab52f716e4c17e070c60d8",
  "rationale": "Round 24: source-to-target permutation control for the gain-aware conditional layer-33 MLP fit.",
  "tensors": {
    "language_model.model.layers.33.mlp.down_proj.weight": {
      "base_sha256": "2d291bc5e5bf8a4a49641d6b3994bdcf3009ff6874a7591c6274f3ff8f302858",
      "changed": 312645,
      "content_sha256": "68fa5e921b1d330dac5cfaf2fa3402c18f29cd04de228b05b27fafa742146a34",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "dbe9de5d5d4eb2a31b88993c18fefad68a76e2c757ab18d8c1b48566714e432f.npz",
      "sha256": "0039dce7bd5d4cb91f49e04de15d4bb3d26642b3f826a956927073be246413e2",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 312645
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-589644f45f380ff6e94113f8a53bd6f747b4ae9fd83ef493da0164ea43cff0fe",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4331896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第25轮

**当时目的与操作理由（原文）**

Round 25: preselected disjoint matched-column control for the conditional layer-33 MLP correction.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 311106,
  "id": "c-de828d06a785aecb5a7746ec583804f76ecd1219d7eda3b71c04ad66b35ed196",
  "l2": 3.318860583265865,
  "parent": "c-589644f45f380ff6e94113f8a53bd6f747b4ae9fd83ef493da0164ea43cff0fe",
  "rationale": "Round 25: preselected disjoint matched-column control for the conditional layer-33 MLP correction.",
  "tensors": {
    "language_model.model.layers.33.mlp.down_proj.weight": {
      "base_sha256": "2d291bc5e5bf8a4a49641d6b3994bdcf3009ff6874a7591c6274f3ff8f302858",
      "changed": 311106,
      "content_sha256": "6b762a7cdc87bfbac257aafbedff00f6c29c6dceca1e63bbf11c0e8a57e603dc",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "dbe9de5d5d4eb2a31b88993c18fefad68a76e2c757ab18d8c1b48566714e432f.npz",
      "sha256": "36a6d14c81de0d59a3e70bbb3074c714b7d29aefae71b93d02f03e7cc2b4f971",
      "shape": [
        2560,
        10240
      ],
      "stored_coordinates": 311106
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-de828d06a785aecb5a7746ec583804f76ecd1219d7eda3b71c04ad66b35ed196",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4331896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第26轮

**当时目的与操作理由（原文）**

Round 26: sparse, supervised final-block MLP output-gain correction, reconstructed from W0.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 256,
  "id": "c-0f5f88848fb6bef8fa9e134f632fa6828bb3f5d3ab2228d47b1b10dccf612b8c",
  "l2": 184.08499438099238,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Round 26: sparse, supervised final-block MLP output-gain correction, reconstructed from W0.",
  "tensors": {
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 256,
      "content_sha256": "bf009636e098968d7fdfce684efb9c23028eb1040334fee9b6e6106980d20032",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "3b0c04dd05fa27e9d4dea4732801860e6815d8bdc7c4383fcf3eecc6fe829ca3",
      "shape": [
        2560
      ],
      "stored_coordinates": 256
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-0f5f88848fb6bef8fa9e134f632fa6828bb3f5d3ab2228d47b1b10dccf612b8c",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4331896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 5,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第27轮

**当时目的与操作理由（原文）**

Round 27: predeclared fourfold dose of the fixed sparse block-33 MLP output-gain correction.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 256,
  "id": "c-e45b96d9e6e9e1a0a221f66d62a6bb161177967a81486263010e3fb593fcd389",
  "l2": 736.1360082595131,
  "parent": "c-0f5f88848fb6bef8fa9e134f632fa6828bb3f5d3ab2228d47b1b10dccf612b8c",
  "rationale": "Round 27: predeclared fourfold dose of the fixed sparse block-33 MLP output-gain correction.",
  "tensors": {
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 256,
      "content_sha256": "fc5aec14765bb497cb6e425cb3864c93c855f897cec36cbf7f0528b0e2a0c845",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "8813721708ed15468de231dfcb7387657c241a4496343361fb7e70b8a55d51f8",
      "shape": [
        2560
      ],
      "stored_coordinates": 256
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-e45b96d9e6e9e1a0a221f66d62a6bb161177967a81486263010e3fb593fcd389",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.43103448275862066,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 5,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第28轮

**当时目的与操作理由（原文）**

Round 28: predeclared opposite-sign control for the sparse final-block gain correction.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 256,
  "id": "c-13e2f16c7a5f5562043f7bd002218c05d939c34e0fb2c35bd3162496d9aa905b",
  "l2": 735.9089431826807,
  "parent": "c-e45b96d9e6e9e1a0a221f66d62a6bb161177967a81486263010e3fb593fcd389",
  "rationale": "Round 28: predeclared opposite-sign control for the sparse final-block gain correction.",
  "tensors": {
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 256,
      "content_sha256": "c39bf7778dd8647287050d5db048ecc98d200250bb323ecc8f25ac258b376ae2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "6ef9fe1bd312aa4e67cbe5ba584d8a2188296328b1d4c3d8785fa1936293b375",
      "shape": [
        2560
      ],
      "stored_coordinates": 256
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-13e2f16c7a5f5562043f7bd002218c05d939c34e0fb2c35bd3162496d9aa905b",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4353448275862069,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第29轮

**当时目的与操作理由（原文）**

Round 29: predeclared gain-stratified permutation control for the sparse final-block gain correction.

**本轮原记录的主分数**：`0.15517241379310345`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Format/truncation protection failed"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 256,
  "id": "c-66463e76e784ed48e09eb01dc7a6a1443449d036e82de8e4ab9da2bc1d1e2a44",
  "l2": 736.1728690763213,
  "parent": "c-13e2f16c7a5f5562043f7bd002218c05d939c34e0fb2c35bd3162496d9aa905b",
  "rationale": "Round 29: predeclared gain-stratified permutation control for the sparse final-block gain correction.",
  "tensors": {
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 256,
      "content_sha256": "9a49d23ab61c0ed52a90b192d82c547552952ad20dec38c5d8b1f08c6acda013",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "3bba1baf493a2619a5a1b5f7ae25ab1fac6a97b035d6921cfeeefaf4a731d4fc",
      "shape": [
        2560
      ],
      "stored_coordinates": 256
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-66463e76e784ed48e09eb01dc7a6a1443449d036e82de8e4ab9da2bc1d1e2a44",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.43103448275862066,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 33,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 5,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第30轮

**当时目的与操作理由（原文）**

Round 30: predeclared disjoint matched-coordinate control for the sparse final-block gain correction.

**本轮原记录的主分数**：`0.16379310344827586`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Candidate does not improve the frozen selection rule"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 256,
  "id": "c-e7e1b0c14054fe386e7a02cd0b41db40e1b5b0d41d843e7fac13799898a7db10",
  "l2": 736.1962867715715,
  "parent": "c-66463e76e784ed48e09eb01dc7a6a1443449d036e82de8e4ab9da2bc1d1e2a44",
  "rationale": "Round 30: predeclared disjoint matched-coordinate control for the sparse final-block gain correction.",
  "tensors": {
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 256,
      "content_sha256": "33537c9d6039e351475588e7755355c95497e144a1bdf5f3bd590eeb30f2ec62",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "5e6bf45e37f6f1463543881219ee33af7fdc64f1073fc490f9220cc19af1ab01",
      "shape": [
        2560
      ],
      "stored_coordinates": 256
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-e7e1b0c14054fe386e7a02cd0b41db40e1b5b0d41d843e7fac13799898a7db10",
  "full_development": true,
  "protocol": "e3ba1ed45f1f2145e30d1e496dd9b918e56e7c6b51e26bdec65107f6aeda65bf",
  "summary": {
    "accuracy": 0.4331896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

