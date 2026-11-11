# Gemma-v8-B：逐轮目的、修改与结果

本页逐轮转录已归档值，不重新评分、不运行模型。共30个完整候选；不是新增30次实验。研究者当时的理由按原文保留，其中预期不能读作已验证结果。每轮均从其记录指定的基线和父候选解释，不能默认累加补丁。

原始完整档案（含逐题答案）：

- [experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1010/B-remote-evidence.tar.gz](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1010/B-remote-evidence.tar.gz)

## 第1轮

**当时目的与操作理由（原文）**

Causal visual-gain test: change only multimodal RMSNorm weights to 1.10*(1+w0)-1, based on measured normalization semantics. No label fitting or target-model training. Test whether stronger image features improve heterogeneous count/spatial errors while protecting all cells.

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
  "changed_scalars": 1147,
  "id": "c-d4a0aedd1492f3ecc8016281c1ed14dba97eb891fb524f02650548684ea0dcb1",
  "l2": 3.6603481514105574,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Causal visual-gain test: change only multimodal RMSNorm weights to 1.10*(1+w0)-1, based on measured normalization semantics. No label fitting or target-model training. Test whether stronger image features improve heterogeneous count/spatial errors while protecting all cells.",
  "tensors": {
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "297ed0686392e2bb01be5cefd84cce8626d6e0087412f9781f29ef4bcfd4f645",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "d350a04bf56f91770eb87b354dea7f39042da14d65f4070ba1a71126be57b1f3",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-d4a0aedd1492f3ecc8016281c1ed14dba97eb891fb524f02650548684ea0dcb1",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.41163793103448276,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 27,
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
        "correct": 37,
        "n": 58
      }
    },
    "format_errors": 6,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.15517241379310345,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第2轮

**当时目的与操作理由（原文）**

Opposite-direction causal test after 1.10 gain worsened full-development performance: set bridge RMSNorm to 0.90*(1+w0)-1. No other changes, label fitting, or training. Test whether reduced visual gain mitigates overcounting without sacrificing protected controls.

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
  "changed_scalars": 1147,
  "id": "c-72a35850e310e27e1792f2dbf939988f108c5328a48a4027722f883b6b0717a3",
  "l2": 3.661003704488157,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Opposite-direction causal test after 1.10 gain worsened full-development performance: set bridge RMSNorm to 0.90*(1+w0)-1. No other changes, label fitting, or training. Test whether reduced visual gain mitigates overcounting without sacrificing protected controls.",
  "tensors": {
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "2cf06d47aaee6afbfe3fd749531c1b0c50837eae4877c7a473fb1c5e351f5244",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "45266f873a7f1dc3f20faa2897302906ddde001934f7e3c4e2c58ee84e7c1dbf",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-72a35850e310e27e1792f2dbf939988f108c5328a48a4027722f883b6b0717a3",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.44396551724137934,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 30,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
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
    "repair_score": 0.16379310344827586,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第3轮

**当时目的与操作理由（原文）**

Independent attention-concentration test motivated by 0/92 correctness on empty spatial subsets despite 4/4 category-absence zeros. Uniformly set all 34 decoder q_norm vectors to 1.05*(1+w0)-1; vision and other parameters unchanged. No layer ranking, label fitting, or training. Does not assume attention is the established failure mechanism.

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
  "changed_scalars": 8428,
  "id": "c-8d74950184ed23e1d430819f7fd15bf572a4a322959ca7f6c12787cd21dcfcac",
  "l2": 7.438399117141244,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Independent attention-concentration test motivated by 0/92 correctness on empty spatial subsets despite 4/4 category-absence zeros. Uniformly set all 34 decoder q_norm vectors to 1.05*(1+w0)-1; vision and other parameters unchanged. No layer ranking, label fitting, or training. Does not assume attention is the established failure mechanism.",
  "tensors": {
    "language_model.model.layers.0.self_attn.q_norm.weight": {
      "base_sha256": "6401b2c7c5bfab11529fb704460adb7dad8e2970178bdf750d082214b04e461a",
      "changed": 249,
      "content_sha256": "d333fe6241fc3dce47078b191df3fdac3e05afcbc3990e5d2b579f91c97031ba",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "8dd70d9750331d003d9fbe1a3822afe2205e5454663f37f29a654530db8cca4d.npz",
      "sha256": "7c69052987b2be141d58da407cf2a1266c63828fa3028136325140228c4968c2",
      "shape": [
        256
      ],
      "stored_coordinates": 249
    },
    "language_model.model.layers.1.self_attn.q_norm.weight": {
      "base_sha256": "7f359bb1d21841c2f827594b98b3eb1b55d54814fa0ad7bf9f4b995c350937a8",
      "changed": 249,
      "content_sha256": "7f3abcc0be67384be22a90039fcac596537f811eff2f5233d6c9d7f9840a0c13",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "183182034e58a3d25bb1cc9fd6d97db28ef00a929d376ab43ef7bad6407d392d.npz",
      "sha256": "257a2e71d98df23a21cee15f7c85239d9db3e2f491fbaedf1eeae041c1b533a4",
      "shape": [
        256
      ],
      "stored_coordinates": 249
    },
    "language_model.model.layers.10.self_attn.q_norm.weight": {
      "base_sha256": "73c783fb13bdccff7118a31986d628e87af113be2a6996323d2813759b6102fb",
      "changed": 252,
      "content_sha256": "2612223aed20cfab77dbaf6ba2e88df43d793f12b7e27d9d8f99fdf117ae3c38",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "bb2560638edf12c41ff5000286adc91ddf224c458158146b39068d1aa2255d9e.npz",
      "sha256": "305bdd9071e2efdc1d8623a063216311a59d46fe87d5d57a85ee23815d36273c",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.11.self_attn.q_norm.weight": {
      "base_sha256": "4dee1e2bfd0ed32693f4325c8e4e3db562045b69ae54fbbe4fa0312551466fb9",
      "changed": 246,
      "content_sha256": "26019bd7d55fcf6e6b49a9c06020b36229ac9ebae298698ea875ca997f12965f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "607adf4d60f2b81a3a81ea849f3c08025be0ed37d6ad197cd2794275f5c091ea.npz",
      "sha256": "fec326f77ad0497269eec1e4dee17f4225ec8191949a2d5521902782d637943d",
      "shape": [
        256
      ],
      "stored_coordinates": 246
    },
    "language_model.model.layers.12.self_attn.q_norm.weight": {
      "base_sha256": "e2ea95de7f354475bda9b6b7acf867ed14275aff084978c5576763a83b97cbbc",
      "changed": 252,
      "content_sha256": "3dc06b23c5be7978ef44ff4db13c0b25a750610fbbac107d68891401142bed3f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b1879e772bc38b0f7d765dd18cbc36b89f0532d06ad89b9e8991f60c0260624d.npz",
      "sha256": "26b4910fa47ddb3d5bfab7b4fb7bc4a3206a0f73035f9b72b040001501c3456e",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.13.self_attn.q_norm.weight": {
      "base_sha256": "092dec87122cb6f174dd76b2b3eac0d9e17f46617a3a3e7778a5a9c3bd0c7066",
      "changed": 250,
      "content_sha256": "731fb4602528d30cef05c09b4ab29d22d8e77ee6bb8c934d9514b712644473c1",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ef317e94f5be3c43904dbf591c59ca48f429f633940f82ccafeb7bf60315725c.npz",
      "sha256": "653215f3cf90997d38cd4fbe5799312aecea5bbeea98b087e2fe55e9b0cbfd77",
      "shape": [
        256
      ],
      "stored_coordinates": 250
    },
    "language_model.model.layers.14.self_attn.q_norm.weight": {
      "base_sha256": "43f4cc337dd24901f956b888010d183d4efedba0a86b0e9c6ac2a767cb224ab3",
      "changed": 253,
      "content_sha256": "799c6a25b45f8a06ae6a5d77a7b2d349bbb13567cbdb3b04de366195163981df",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "2111c4f0c8af8092982e9c69ce4b5318e8c10e385b8a5b1bb86903acb1dbe5a7.npz",
      "sha256": "44edbc97ac7e441a70f4eef908d98304069fd0d031570d7d9773399fa7e5e23a",
      "shape": [
        256
      ],
      "stored_coordinates": 253
    },
    "language_model.model.layers.15.self_attn.q_norm.weight": {
      "base_sha256": "4c2102f5f534a50f9801e93f3746adb171c6cb55b722b5f951dd5149b3916f1e",
      "changed": 246,
      "content_sha256": "8221eee005f08a2ea2b113fe27c06616bda60f8a86b5de4b174936edc3fba205",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "33a36c166bf6b2abac5bbe6668ceca19df1cf1dc2b7da397d284c3b4560f2316.npz",
      "sha256": "31217eacfd69ca75691e395c0d669dcfc3790f162e64d7a9284b3a845ffe593c",
      "shape": [
        256
      ],
      "stored_coordinates": 246
    },
    "language_model.model.layers.16.self_attn.q_norm.weight": {
      "base_sha256": "7ed8456e7cd543fa5304c2a4bc56cbf8928fe816ed1b02422ee3b818291a1919",
      "changed": 252,
      "content_sha256": "1c407303e113c4bbec5e09c8c8a42ab91bcac10e50885ccaa8312bf44efa1df2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "906d01e6e07c55ee3a9fe1a32985aee91c488453bcdd9ac791b88af8e88abfcf.npz",
      "sha256": "4b4b1bc5f0456bd140c8fbccb5ee87fbac96b269fea02f4a0353539e26c53442",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.17.self_attn.q_norm.weight": {
      "base_sha256": "29197088a4f72f53a39664c600ba32da8770a0a1f0a9f1100af6987b67c17766",
      "changed": 234,
      "content_sha256": "9cf315abe25f36a6d963f326f5f3cde32ff12f21e5a89cb529caa9caf54beb7f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4bce20f1ea03d0453c495caebeec6eb83c91daf1373809a6ad792674ed4b8a59.npz",
      "sha256": "ea6c673bc2dadfe3dfa4c771ab0b897e0c3594beb6bf50e4de4e6bff33cb3b5d",
      "shape": [
        256
      ],
      "stored_coordinates": 234
    },
    "language_model.model.layers.18.self_attn.q_norm.weight": {
      "base_sha256": "6419abb8a38f327be240936750298b5c1cf2dcd7d85c11e971711793384cd05a",
      "changed": 254,
      "content_sha256": "d22d0fe81f2f7a927a58f9a2dd0945d27cf39ce73a8bfa46739d28411a51ff1d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d7a8d946f24d0cfba26eca1bb36567d322eb9365875abbbf2fdd09d11a697072.npz",
      "sha256": "b674c18488caf0fc3b149586cf5b8ef84708719814bceff8665437f8375c7c63",
      "shape": [
        256
      ],
      "stored_coordinates": 254
    },
    "language_model.model.layers.19.self_attn.q_norm.weight": {
      "base_sha256": "ca264f3b4e3539f5fafdac989117b17dcc9d75f49529d6a6a161002123251a68",
      "changed": 249,
      "content_sha256": "a1c350713edcadca51491466800c8191a93df398c332e022ceba118557269395",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4818e56e7777e709295056ed13f612163e19f6859b6d7c989cd296445b517ec5.npz",
      "sha256": "e5bb6d28be93530070998e2f399944010c3d966be941116cc80208897e8e03da",
      "shape": [
        256
      ],
      "stored_coordinates": 249
    },
    "language_model.model.layers.2.self_attn.q_norm.weight": {
      "base_sha256": "64ae04fe47c0042899e9e959163cee1db44735ab794c58d5d930430592a806e0",
      "changed": 252,
      "content_sha256": "8ba1a9905db9fafbe777aa715beddbdd9c968162c40a1d502c6a85bada0dad2c",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d20048058bb966463880edba0b79e540a4fe8e3af21f152366da6ee30ae5f09e.npz",
      "sha256": "640cd3da3739209a74a984ca5d97cf4c0a07ba280727e6c03f7cf99f37f52857",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.20.self_attn.q_norm.weight": {
      "base_sha256": "6a769b7e71fe00f073a9c96c0796370653fa8a70e101c408f1c9684613a3ee21",
      "changed": 252,
      "content_sha256": "f5e3f83f778d1be8f5d95d6dfa80c7bf8ef0b52112238e243189a57927186d4a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "6f8395ecfce30f57b4191695ee4767c143380cc7171ecd81e648c80141f71be8.npz",
      "sha256": "0f0f25befc9640cde0773dab4e74c47eb4a169ed2d37855f408fa6f40c6a381f",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.21.self_attn.q_norm.weight": {
      "base_sha256": "76c9dd4664c91532b73ee92e099b7379ce2b7e7dee762b04f056acb333b355b4",
      "changed": 246,
      "content_sha256": "1108e103258d0ef9ac842611ff2410e742566b628ab3340992ac5d763042887f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4a2381724cd1b7a8f48d8e2bcddda5f3151b4d7779287a9b79604f592f48de65.npz",
      "sha256": "43652939817871b8e3665dabf715c7eed47bbcc07f65bd3c74fe40d4d77d4ae7",
      "shape": [
        256
      ],
      "stored_coordinates": 246
    },
    "language_model.model.layers.22.self_attn.q_norm.weight": {
      "base_sha256": "7c0a7577ba30a4967d04985c2111daca74824abeb320d03a199cfe88d869ff19",
      "changed": 253,
      "content_sha256": "07f2805a59674f14a34efe132d8433bfab4da97bfc48fb7bebf61d244e72a15b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4cca51d54fcac272c9216509bc31bce5218ca4cef4e46d62f4afc90c74ff5d34.npz",
      "sha256": "b5e720c4944b7b5923100ec29dc37ceca4c751743319bc9190b27f58873effa5",
      "shape": [
        256
      ],
      "stored_coordinates": 253
    },
    "language_model.model.layers.23.self_attn.q_norm.weight": {
      "base_sha256": "8954fc963f9319d12cebfdfd498cd401b19f49b8e968f3a3369f35b13bc6de5f",
      "changed": 235,
      "content_sha256": "9238b8ba2bacbd01b6e03532c413c9c3e128d18c13616c1951326331aa751ec8",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "e0cf5c40d6d0ee83b23ed482fbc3aafad23aaa57d39efc0758443ad52a4e5ab1.npz",
      "sha256": "e11a7e39c0243971953233cbd32afc92d3ef85d14a2c72b9a3a546ba0e50e30e",
      "shape": [
        256
      ],
      "stored_coordinates": 235
    },
    "language_model.model.layers.24.self_attn.q_norm.weight": {
      "base_sha256": "828849f9d6b5239e70716b06a43fd8c3219ee915aca45c856d9adf0b8544d29d",
      "changed": 246,
      "content_sha256": "718d3d8bb919c60bff21baa0c2f0fd6a419c2687b877f911700c4be7cd651ea4",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d861f20b6f00275f8331fd6915c99bea1319a1d4394e81641db3681129ae147a.npz",
      "sha256": "1a9f05ae3082eb5e4055ae841d248b2cf44a51fbbefd9b033f242a58bc199b2b",
      "shape": [
        256
      ],
      "stored_coordinates": 246
    },
    "language_model.model.layers.25.self_attn.q_norm.weight": {
      "base_sha256": "86b3c0b01c295125ae2a94098aa41545c28eda8be605e15eb26e37309aa81f74",
      "changed": 251,
      "content_sha256": "cb7c199d0f4ed46ba9bd38d7d85dc42355dae40f1e236d37f99d8116d8084e77",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ae1ff1e282485142fb28e10e9bc97b5da2f87b0a0e8b4a9e98d65cbd00ef449a.npz",
      "sha256": "17dbdaf19328a97e985e111c31759d4b48113a01df29a5b3e7058394dc0b3749",
      "shape": [
        256
      ],
      "stored_coordinates": 251
    },
    "language_model.model.layers.26.self_attn.q_norm.weight": {
      "base_sha256": "96202abf3152b88361d99faf7ed6c80a0e46b8e07e3b099ef91c39cda650531c",
      "changed": 230,
      "content_sha256": "aabb3dc767f5b56684cc17361bc98b5ee79bb911108014f96baf3a1ade03923e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "046c3c7e5ba0b51022f33fe051f9a0007ad92bb4bff4fc312f1783525b097389.npz",
      "sha256": "94aa6458381bd7c4b0c1cf4ef892935750e9c7bc1a5dbf7627d31621c5e35859",
      "shape": [
        256
      ],
      "stored_coordinates": 230
    },
    "language_model.model.layers.27.self_attn.q_norm.weight": {
      "base_sha256": "8b915b92fdb330c3c9a6681a348cef9c1d2db9461b6d96472072bfdc3cd47160",
      "changed": 247,
      "content_sha256": "073d8de687bb29f6fda6d79f3b47ebe78c5052071cd7c654f2c43bbea8108fae",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "35d02ef99ed39dd9e59ba4b3f2b520a4579ff57245bdbee950ea1b4f8c02db06.npz",
      "sha256": "036075974369b518d3f851d8b6d3c05adece8114299099af54b4efd2ea7bc749",
      "shape": [
        256
      ],
      "stored_coordinates": 247
    },
    "language_model.model.layers.28.self_attn.q_norm.weight": {
      "base_sha256": "da5dc3ba07b30c4469349d8ed5be5ddf86e60217624f63649c9ea699b3cabb0c",
      "changed": 249,
      "content_sha256": "756001767c8665aa55619f25b486fc4111809ba211b653a9b67e410050adaab7",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "f41360a1a9a4b34e585315bb3c1303e26e9e1370fd2997e77a7d3c3932d73532.npz",
      "sha256": "8a83324fd63efcfb75bb98530f14348e0fe06ed6623f2facbbd875d752cf29c9",
      "shape": [
        256
      ],
      "stored_coordinates": 249
    },
    "language_model.model.layers.29.self_attn.q_norm.weight": {
      "base_sha256": "21c98d1d1a44534adb25a3394e339198d6ea7d354cff4bb9320d361e4bba6d49",
      "changed": 231,
      "content_sha256": "635829d3d6cb2f8bf487c4516a663f44e7dc42ad81a848ea5bd6e6de0f21031b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "279b96fa7ca2b8552983493fcd55c7bef30849bb8898a473b6c3586ed576f01b.npz",
      "sha256": "07348714c2b4b1537e9fe76b2d407cde9212fdc6487e0bb06bb8477d164b9d55",
      "shape": [
        256
      ],
      "stored_coordinates": 231
    },
    "language_model.model.layers.3.self_attn.q_norm.weight": {
      "base_sha256": "83c3f6133d5a8ec9824c0aef9223e7d36685e1b4b13db47ccf1c0572e7a3a524",
      "changed": 253,
      "content_sha256": "f33bca36c9499ba6e5b01f516ad2a20c82ac0949b229710080ed951e1e0cb955",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "bc0ff3cd868e26c9776fbf7943100f959568a9f922cc6fa2b76341b83905f0e9.npz",
      "sha256": "4810295df814719903e039b29d7fcddac82bc59c1e8f67569e32c34f2a0c9080",
      "shape": [
        256
      ],
      "stored_coordinates": 253
    },
    "language_model.model.layers.30.self_attn.q_norm.weight": {
      "base_sha256": "8081d42a39ff6c7d630f75839344920c6a7ddb2b30ad2e6a4daee13b861a8aba",
      "changed": 230,
      "content_sha256": "588898ad73fc2852f8e307322e5285f9436c7c4f8db1c014107cfde6be82f97b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "6717a3d9b197c5e046055c34b002b3f17f3ac876e8e038dc2212ef6dff789ed8.npz",
      "sha256": "5f8f99379b6d1352297900d7c8b60143a74eda5a049a08d66e5af76f41916daa",
      "shape": [
        256
      ],
      "stored_coordinates": 230
    },
    "language_model.model.layers.31.self_attn.q_norm.weight": {
      "base_sha256": "d3b93b88e19b3b269de41c9eec75c2512b9c89969ede6876ac47f3c32a153ff0",
      "changed": 255,
      "content_sha256": "9bd668f2870f454105fdd37d3f9be5c1c82fd69175cea734daeb74475fb24863",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "50694872031bd6fdb4facf07140779a9cdd3bd7bc571a4ea90e3677b4705f4ad.npz",
      "sha256": "0e581758aeb9c90fe75039e1af8236c7d32886243f23420a56577ea2f7b780f4",
      "shape": [
        256
      ],
      "stored_coordinates": 255
    },
    "language_model.model.layers.32.self_attn.q_norm.weight": {
      "base_sha256": "316c23acdeea87704ce76401bf414f2be8d6b984e33ded014043016bd806c601",
      "changed": 248,
      "content_sha256": "7c79e75a81a2d1c7f2087379bbf4d47a492ff24891db35575f5ae0ecee7ab835",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "1c78cee4a5e96733af05cb8822b40e2fc703512dd096a706b459b461b868ee80.npz",
      "sha256": "0ea6d3feb499e8da7c48d69ed70945baa52de3329bcb5943afca554bc1f4974f",
      "shape": [
        256
      ],
      "stored_coordinates": 248
    },
    "language_model.model.layers.33.self_attn.q_norm.weight": {
      "base_sha256": "7056fa64146b12ad2d039dbec67f0c711be054b5e87d657a9d2d977af5d4d633",
      "changed": 252,
      "content_sha256": "1576e557e68eda5f14ba8b206ce48b01b43376148dfc4285580c9fb70d6b7dfa",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b0b1e45e17a7797abca11a78aea137d4281b6ccf4765d03d082ded59fa75aa1c.npz",
      "sha256": "820dc26d009bad563bd4a88d53d5d76c2f3e3eff61eb283419a6cf95592864a3",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.4.self_attn.q_norm.weight": {
      "base_sha256": "9a6d91686f80b34e78a64a2b05f74d6813e6042234f6234f94e2d44378d5a4e2",
      "changed": 252,
      "content_sha256": "3cc10b39d280596ca296ac263b08c213d3f2cac1c9791363bf9747e314dbc8dd",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "29172b24d4e9d6bcbc7f7321b00b55818b77fd72f4b67c1df16bd1830df8aefc.npz",
      "sha256": "c96a083181d5eec87632711b131ccf66d8d6f0321ce8dfb1a8b38fd1e2514442",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.5.self_attn.q_norm.weight": {
      "base_sha256": "7884f6dab04d015df873da8d400e58233d8d39dafca27079a7539b69d0982770",
      "changed": 249,
      "content_sha256": "d3c84f79271251dbbd3cbdb8803917f321df52962183a7eb75fbb9df485ef91c",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d2d577f7a0f5fe476e4956889f54e6ccb9b849f710f4cf700dd7f060f4e4f23c.npz",
      "sha256": "f05c9471a8c144da7a44322bb0b5dee5037316d8761f231022f3c25473b74025",
      "shape": [
        256
      ],
      "stored_coordinates": 249
    },
    "language_model.model.layers.6.self_attn.q_norm.weight": {
      "base_sha256": "7e47a125567be4bc3bc46ec958ac2d0e33ac0b17a2051095d3b2f48dcda53714",
      "changed": 253,
      "content_sha256": "bb6a1a38b6f8c6717771d5020722de9fc68a6c82d8b839fc1e2f41cc417e6c1b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "a2d5a71a7d31a80c81513f8097b59f0d53e8cf1ac6ab541b52ff889db51fa4ff.npz",
      "sha256": "cc448f769f6e8024ef5e91b5a14cb93678e1a4646165ff441259f3023c45332e",
      "shape": [
        256
      ],
      "stored_coordinates": 253
    },
    "language_model.model.layers.7.self_attn.q_norm.weight": {
      "base_sha256": "d889a6d265c731c405bc89a299cf05fddc10680190c4218fd8bb979141d0efe7",
      "changed": 255,
      "content_sha256": "57fd7dab0d5bb702b4858d023fe8193297e1d2d627551298830a43023996fa12",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "a8c03854be343f1a56f1e4489cf255e06314bb1a1aae2516ca482f0f0e4ec6df.npz",
      "sha256": "605188876c6a105ac169d52d35e731f4eff7628fc08da7f1b24bcb05bfc20e44",
      "shape": [
        256
      ],
      "stored_coordinates": 255
    },
    "language_model.model.layers.8.self_attn.q_norm.weight": {
      "base_sha256": "00b1c8cf65281b98812522a5daf583bb9c6657be4e9b74ea15997d7abde6bdd4",
      "changed": 253,
      "content_sha256": "340a203b94854d5a8a2c35cf8a2f77f253aa64bf0bdb7094bf48637155e140eb",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "08712d60469e0e5600c211d55d831343705b0e279af27f4c133fe592f5aca38b.npz",
      "sha256": "852b720a6d612c9aa64ec7fdb79e06edb9bfb057d60ae836c3e442257c9697af",
      "shape": [
        256
      ],
      "stored_coordinates": 253
    },
    "language_model.model.layers.9.self_attn.q_norm.weight": {
      "base_sha256": "a9c4efebb989e834d80704edcf5ba0392d729f5f4481362927716cf33fb97125",
      "changed": 250,
      "content_sha256": "976e28506abaaf614d582bb119f337a82198f77635cc3e18d0a91106c64ac196",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "f4855499d40919174731fa081408f83e7ed088b1d44d397a661727fb1c6d659f.npz",
      "sha256": "c158377d61ecf69093527dbea2fab045ab6cf47c1e2595533fc236be712cc5a6",
      "shape": [
        256
      ],
      "stored_coordinates": 250
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-8d74950184ed23e1d430819f7fd15bf572a4a322959ca7f6c12787cd21dcfcac",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.43103448275862066,
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
        "correct": 19,
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
        "correct": 30,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 41,
        "n": 58
      }
    },
    "format_errors": 6,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第4轮

**当时目的与操作理由（原文）**

Symmetric follow-up to failed attention sharpening: set all decoder q_norm weights to 0.95*(1+w0)-1. Test more distributed context integration while keeping image features and every other parameter fixed. No label fitting or target-model training; development feedback motivated this scalar setting.

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
  "changed_scalars": 8428,
  "id": "c-ef778263c3970443f9249d3c42a6c2c502adae7d10e1ad6151c04e5453bf039c",
  "l2": 7.448347706423412,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Symmetric follow-up to failed attention sharpening: set all decoder q_norm weights to 0.95*(1+w0)-1. Test more distributed context integration while keeping image features and every other parameter fixed. No label fitting or target-model training; development feedback motivated this scalar setting.",
  "tensors": {
    "language_model.model.layers.0.self_attn.q_norm.weight": {
      "base_sha256": "6401b2c7c5bfab11529fb704460adb7dad8e2970178bdf750d082214b04e461a",
      "changed": 249,
      "content_sha256": "e2a87a8e5a5fcd43373a9b30a5880d85dcd685f05f5dc962b0287667fe17cccb",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "8dd70d9750331d003d9fbe1a3822afe2205e5454663f37f29a654530db8cca4d.npz",
      "sha256": "8bd06eea93b8f203883e4a693f8cb7905e0cb5fb8d16b245c47dac92dba21114",
      "shape": [
        256
      ],
      "stored_coordinates": 249
    },
    "language_model.model.layers.1.self_attn.q_norm.weight": {
      "base_sha256": "7f359bb1d21841c2f827594b98b3eb1b55d54814fa0ad7bf9f4b995c350937a8",
      "changed": 249,
      "content_sha256": "8577731dfed51223ac1df857c74f22bb0bf8dbafaf2f8a8fd69c5ecd011f763e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "183182034e58a3d25bb1cc9fd6d97db28ef00a929d376ab43ef7bad6407d392d.npz",
      "sha256": "57ee1d8f00ea14f75a5b65cb69f745eebb81eeaf4d0b3155905ef4e8737e97df",
      "shape": [
        256
      ],
      "stored_coordinates": 249
    },
    "language_model.model.layers.10.self_attn.q_norm.weight": {
      "base_sha256": "73c783fb13bdccff7118a31986d628e87af113be2a6996323d2813759b6102fb",
      "changed": 252,
      "content_sha256": "de19257f39338961e94f96da6760c365ae6c8cca86b1cb0f84150cfc8f1eb5e6",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "bb2560638edf12c41ff5000286adc91ddf224c458158146b39068d1aa2255d9e.npz",
      "sha256": "88a6f4cd8a798a75d411b9ecff06293bea449228ec637c3d35f80ab803d1e079",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.11.self_attn.q_norm.weight": {
      "base_sha256": "4dee1e2bfd0ed32693f4325c8e4e3db562045b69ae54fbbe4fa0312551466fb9",
      "changed": 246,
      "content_sha256": "135350e8fc9fed68abe85ad32fac84492ca6546711bc64cb44e087c57e49ed52",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "607adf4d60f2b81a3a81ea849f3c08025be0ed37d6ad197cd2794275f5c091ea.npz",
      "sha256": "df3c50651f1a2f5daa7fa11c6f7150a3a9aed1e2908c66c04e1ab854a76a527d",
      "shape": [
        256
      ],
      "stored_coordinates": 246
    },
    "language_model.model.layers.12.self_attn.q_norm.weight": {
      "base_sha256": "e2ea95de7f354475bda9b6b7acf867ed14275aff084978c5576763a83b97cbbc",
      "changed": 252,
      "content_sha256": "e6c9584e2d0a78aa2a94163d30952141c7e77f0769a2b9d0c0e09527d4f3b873",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b1879e772bc38b0f7d765dd18cbc36b89f0532d06ad89b9e8991f60c0260624d.npz",
      "sha256": "636400872b7ad413e4cedc3c94a70389940dd5c8e2ef34a90fbdc466d9b06b87",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.13.self_attn.q_norm.weight": {
      "base_sha256": "092dec87122cb6f174dd76b2b3eac0d9e17f46617a3a3e7778a5a9c3bd0c7066",
      "changed": 250,
      "content_sha256": "8ccfa3ff2a6c5720d29f487ed5174dbf3f3e3d5edf3a9dfb75c1187dfb29a7e2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ef317e94f5be3c43904dbf591c59ca48f429f633940f82ccafeb7bf60315725c.npz",
      "sha256": "3b7623a074b1749d9faddd3803c00dc8d54f718154b03faaa0c67433851c3250",
      "shape": [
        256
      ],
      "stored_coordinates": 250
    },
    "language_model.model.layers.14.self_attn.q_norm.weight": {
      "base_sha256": "43f4cc337dd24901f956b888010d183d4efedba0a86b0e9c6ac2a767cb224ab3",
      "changed": 253,
      "content_sha256": "d0b39984abdf850580ce0b144461204d2163ca4c35f0016763924a5b4fbbcb9f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "2111c4f0c8af8092982e9c69ce4b5318e8c10e385b8a5b1bb86903acb1dbe5a7.npz",
      "sha256": "2ec442a22f942a6e7b931827b267a3ef375e8a786818dcb1860964ac5c572fab",
      "shape": [
        256
      ],
      "stored_coordinates": 253
    },
    "language_model.model.layers.15.self_attn.q_norm.weight": {
      "base_sha256": "4c2102f5f534a50f9801e93f3746adb171c6cb55b722b5f951dd5149b3916f1e",
      "changed": 246,
      "content_sha256": "30640105091e5cb153339a6221c685faf376a41d9395d7de6e3f0e84fdfcb378",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "33a36c166bf6b2abac5bbe6668ceca19df1cf1dc2b7da397d284c3b4560f2316.npz",
      "sha256": "210e271257064eb26f9582fd752216547e467e752b4c089aa8b63af807514723",
      "shape": [
        256
      ],
      "stored_coordinates": 246
    },
    "language_model.model.layers.16.self_attn.q_norm.weight": {
      "base_sha256": "7ed8456e7cd543fa5304c2a4bc56cbf8928fe816ed1b02422ee3b818291a1919",
      "changed": 252,
      "content_sha256": "6bdb45be6c0f6e03644e87ae4d09c5eca133ba7261f2bb9ae31c437408e4f098",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "906d01e6e07c55ee3a9fe1a32985aee91c488453bcdd9ac791b88af8e88abfcf.npz",
      "sha256": "eb780750ba5ca096deb66992a8db993f2222df479eebb9e05f9970058466d166",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.17.self_attn.q_norm.weight": {
      "base_sha256": "29197088a4f72f53a39664c600ba32da8770a0a1f0a9f1100af6987b67c17766",
      "changed": 234,
      "content_sha256": "64a20a1f8949ed01ad7d292619edc0a15b9ac34165ce5968fc5892c5e106ac82",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4bce20f1ea03d0453c495caebeec6eb83c91daf1373809a6ad792674ed4b8a59.npz",
      "sha256": "f7110ffac4ecf89de10f9d837d646419eb919c8b4eb529ad1620916cbab91b61",
      "shape": [
        256
      ],
      "stored_coordinates": 234
    },
    "language_model.model.layers.18.self_attn.q_norm.weight": {
      "base_sha256": "6419abb8a38f327be240936750298b5c1cf2dcd7d85c11e971711793384cd05a",
      "changed": 254,
      "content_sha256": "2695f7113102440dc046355b2e042baf1e8acfeabd15edea0d7729ae53ee7a8a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d7a8d946f24d0cfba26eca1bb36567d322eb9365875abbbf2fdd09d11a697072.npz",
      "sha256": "462cd39cecd0fc11301ce219b7e3fe141d5da37f3d1a975fc2593b125824a64f",
      "shape": [
        256
      ],
      "stored_coordinates": 254
    },
    "language_model.model.layers.19.self_attn.q_norm.weight": {
      "base_sha256": "ca264f3b4e3539f5fafdac989117b17dcc9d75f49529d6a6a161002123251a68",
      "changed": 249,
      "content_sha256": "5b3a33fcf8dc75b0a00857cfdb06d80b2e50c6df95563042c34c40bca5b08bbc",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4818e56e7777e709295056ed13f612163e19f6859b6d7c989cd296445b517ec5.npz",
      "sha256": "d56c90946f9f29e57d763ce3d2086488f170ab7ad42dbbe7c332de507902eb42",
      "shape": [
        256
      ],
      "stored_coordinates": 249
    },
    "language_model.model.layers.2.self_attn.q_norm.weight": {
      "base_sha256": "64ae04fe47c0042899e9e959163cee1db44735ab794c58d5d930430592a806e0",
      "changed": 252,
      "content_sha256": "3f6c6b1616c34e56d93678c2c6240990e406fd1b47eb0a91130c3dac3d5d7081",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d20048058bb966463880edba0b79e540a4fe8e3af21f152366da6ee30ae5f09e.npz",
      "sha256": "0e337df559099c819505d311c818fc9fe762cacfc08cd33aef4b6baac88472f3",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.20.self_attn.q_norm.weight": {
      "base_sha256": "6a769b7e71fe00f073a9c96c0796370653fa8a70e101c408f1c9684613a3ee21",
      "changed": 252,
      "content_sha256": "6a91398b4b3771808fc041a619a7720677e470f3c0bf7a360e6bd026345a288b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "6f8395ecfce30f57b4191695ee4767c143380cc7171ecd81e648c80141f71be8.npz",
      "sha256": "51ab96e38cd8f2605c2b00bbd0aee8ed5f63bc88c26dfcd6e5497450a960e308",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.21.self_attn.q_norm.weight": {
      "base_sha256": "76c9dd4664c91532b73ee92e099b7379ce2b7e7dee762b04f056acb333b355b4",
      "changed": 246,
      "content_sha256": "5c4ace25fa0182a36f9f233dec3518f1bfccb769ec700ffcff9bc80db24a197a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4a2381724cd1b7a8f48d8e2bcddda5f3151b4d7779287a9b79604f592f48de65.npz",
      "sha256": "fbac320ef3872057b514d22420f466c1973e2403a07986fd22b276c87b8ce539",
      "shape": [
        256
      ],
      "stored_coordinates": 246
    },
    "language_model.model.layers.22.self_attn.q_norm.weight": {
      "base_sha256": "7c0a7577ba30a4967d04985c2111daca74824abeb320d03a199cfe88d869ff19",
      "changed": 253,
      "content_sha256": "d752278c2b957dfeb2c43229a689e29f0d215d3a50855b602849d77868666c7f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4cca51d54fcac272c9216509bc31bce5218ca4cef4e46d62f4afc90c74ff5d34.npz",
      "sha256": "d2ff1fa4a8bf18d8e25f605865a4241ac70b86acd99471f30542c4a9bdf24302",
      "shape": [
        256
      ],
      "stored_coordinates": 253
    },
    "language_model.model.layers.23.self_attn.q_norm.weight": {
      "base_sha256": "8954fc963f9319d12cebfdfd498cd401b19f49b8e968f3a3369f35b13bc6de5f",
      "changed": 235,
      "content_sha256": "f8bfa918c1f87242ff5d551d00d1eb30e22222c7c9737c0199fb1100d472c866",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "e0cf5c40d6d0ee83b23ed482fbc3aafad23aaa57d39efc0758443ad52a4e5ab1.npz",
      "sha256": "6f6fde08ffde64f7817826c75c97413c9320ccea0016a15b33376268ee500929",
      "shape": [
        256
      ],
      "stored_coordinates": 235
    },
    "language_model.model.layers.24.self_attn.q_norm.weight": {
      "base_sha256": "828849f9d6b5239e70716b06a43fd8c3219ee915aca45c856d9adf0b8544d29d",
      "changed": 246,
      "content_sha256": "b4a950d90dd7ea003d565046baa293d9e70fe4abf2eb3fbb2ed3483bbb0dac07",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d861f20b6f00275f8331fd6915c99bea1319a1d4394e81641db3681129ae147a.npz",
      "sha256": "836fd319fb46742e031e3442e0037ac4911ac1170b0d878f5136f78ba83614e1",
      "shape": [
        256
      ],
      "stored_coordinates": 246
    },
    "language_model.model.layers.25.self_attn.q_norm.weight": {
      "base_sha256": "86b3c0b01c295125ae2a94098aa41545c28eda8be605e15eb26e37309aa81f74",
      "changed": 251,
      "content_sha256": "12646906f4634958e1fcb2dacf7095c082bfe4e6b8df055da85b5e30cfd2b5aa",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ae1ff1e282485142fb28e10e9bc97b5da2f87b0a0e8b4a9e98d65cbd00ef449a.npz",
      "sha256": "26ce48091c1b4027ede99df4f124aa1d60ab53d379546f528808ba0a10072691",
      "shape": [
        256
      ],
      "stored_coordinates": 251
    },
    "language_model.model.layers.26.self_attn.q_norm.weight": {
      "base_sha256": "96202abf3152b88361d99faf7ed6c80a0e46b8e07e3b099ef91c39cda650531c",
      "changed": 230,
      "content_sha256": "3b328cb590cdbf71b081837aeab8f5d01377d2dc7adcc0f664e644afc6b84e38",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "046c3c7e5ba0b51022f33fe051f9a0007ad92bb4bff4fc312f1783525b097389.npz",
      "sha256": "b59b21302bb894a02f8f2b8040d3e8108e572e58ad52afa4e98c5427cdd40d57",
      "shape": [
        256
      ],
      "stored_coordinates": 230
    },
    "language_model.model.layers.27.self_attn.q_norm.weight": {
      "base_sha256": "8b915b92fdb330c3c9a6681a348cef9c1d2db9461b6d96472072bfdc3cd47160",
      "changed": 247,
      "content_sha256": "79e57727b2b9a5a6225544245a85adc9ae0702f05bca3dafb4557eaf242e6bbe",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "35d02ef99ed39dd9e59ba4b3f2b520a4579ff57245bdbee950ea1b4f8c02db06.npz",
      "sha256": "d573d39f3a9cd00183bc218ea532a6e5f36c8810ecba6cef2e244dde17606589",
      "shape": [
        256
      ],
      "stored_coordinates": 247
    },
    "language_model.model.layers.28.self_attn.q_norm.weight": {
      "base_sha256": "da5dc3ba07b30c4469349d8ed5be5ddf86e60217624f63649c9ea699b3cabb0c",
      "changed": 249,
      "content_sha256": "fa88fb4f3d17679390e8ed687026711b132086e768d76868477382195b6e110f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "f41360a1a9a4b34e585315bb3c1303e26e9e1370fd2997e77a7d3c3932d73532.npz",
      "sha256": "41ff1a8c6b427e66e478807c323a5e2971beecea183790aeb81a3c235bdbdc0f",
      "shape": [
        256
      ],
      "stored_coordinates": 249
    },
    "language_model.model.layers.29.self_attn.q_norm.weight": {
      "base_sha256": "21c98d1d1a44534adb25a3394e339198d6ea7d354cff4bb9320d361e4bba6d49",
      "changed": 231,
      "content_sha256": "1d267d67420047a3e953c86fa0ade0a746bd7a065cb6997f4ace4c4810f8fbbc",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "279b96fa7ca2b8552983493fcd55c7bef30849bb8898a473b6c3586ed576f01b.npz",
      "sha256": "78f8999cb8153241c09b882ce8f88aa45622a0bdd629a1c6f29e44c04ef03d6c",
      "shape": [
        256
      ],
      "stored_coordinates": 231
    },
    "language_model.model.layers.3.self_attn.q_norm.weight": {
      "base_sha256": "83c3f6133d5a8ec9824c0aef9223e7d36685e1b4b13db47ccf1c0572e7a3a524",
      "changed": 253,
      "content_sha256": "17c1ce232915bd62005ab7ed13b6f6f325136f27f552152e694706c6a1b5e193",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "bc0ff3cd868e26c9776fbf7943100f959568a9f922cc6fa2b76341b83905f0e9.npz",
      "sha256": "c2296daacbc2716b460650c676b17f0881c5082167892e91542af12e413dc384",
      "shape": [
        256
      ],
      "stored_coordinates": 253
    },
    "language_model.model.layers.30.self_attn.q_norm.weight": {
      "base_sha256": "8081d42a39ff6c7d630f75839344920c6a7ddb2b30ad2e6a4daee13b861a8aba",
      "changed": 230,
      "content_sha256": "062b9aec01bc0c45293af8e8b0417374cbbdb6c685491095acf80738599870e2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "6717a3d9b197c5e046055c34b002b3f17f3ac876e8e038dc2212ef6dff789ed8.npz",
      "sha256": "a90f7d629decaa358470e4c80b6570b093e5bab4500d71720e0d7c0e1c3885f0",
      "shape": [
        256
      ],
      "stored_coordinates": 230
    },
    "language_model.model.layers.31.self_attn.q_norm.weight": {
      "base_sha256": "d3b93b88e19b3b269de41c9eec75c2512b9c89969ede6876ac47f3c32a153ff0",
      "changed": 255,
      "content_sha256": "80c63ec00bc7ddfd94e184ebf306e1396b50b592ade459929e2683e5845a68b2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "50694872031bd6fdb4facf07140779a9cdd3bd7bc571a4ea90e3677b4705f4ad.npz",
      "sha256": "1f07adf2220bb63835dd7d3d35aa603e7e69dcb92bb7bceb31d501bc2e25cb62",
      "shape": [
        256
      ],
      "stored_coordinates": 255
    },
    "language_model.model.layers.32.self_attn.q_norm.weight": {
      "base_sha256": "316c23acdeea87704ce76401bf414f2be8d6b984e33ded014043016bd806c601",
      "changed": 248,
      "content_sha256": "67c390ebbe8aab4d6b1c93e0c2c47ffc5153cf95e596cc1574577fcad1f3ae88",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "1c78cee4a5e96733af05cb8822b40e2fc703512dd096a706b459b461b868ee80.npz",
      "sha256": "ec8a4d320f333d74c653c1ef49838371780026c4355066e3651dcd5653002c9b",
      "shape": [
        256
      ],
      "stored_coordinates": 248
    },
    "language_model.model.layers.33.self_attn.q_norm.weight": {
      "base_sha256": "7056fa64146b12ad2d039dbec67f0c711be054b5e87d657a9d2d977af5d4d633",
      "changed": 252,
      "content_sha256": "e78406fdead75207d60768efcc7ced4e5a821b1e5ca295b7616b2cb9f457a558",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b0b1e45e17a7797abca11a78aea137d4281b6ccf4765d03d082ded59fa75aa1c.npz",
      "sha256": "17efecd3842dc3d43fb9fa01ab2834342b4f279eea205d35c55a93042bfbd641",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.4.self_attn.q_norm.weight": {
      "base_sha256": "9a6d91686f80b34e78a64a2b05f74d6813e6042234f6234f94e2d44378d5a4e2",
      "changed": 252,
      "content_sha256": "87028540623b1fcc58899048baa3a689bc7a11665fdb2620bdab484a60ff3d3b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "29172b24d4e9d6bcbc7f7321b00b55818b77fd72f4b67c1df16bd1830df8aefc.npz",
      "sha256": "1811f43674c99034c7e9feddbbd3c3092806acad9de4f095247075e082ca2ef7",
      "shape": [
        256
      ],
      "stored_coordinates": 252
    },
    "language_model.model.layers.5.self_attn.q_norm.weight": {
      "base_sha256": "7884f6dab04d015df873da8d400e58233d8d39dafca27079a7539b69d0982770",
      "changed": 249,
      "content_sha256": "4467e223e73960658402a32923529d2282974a6171a23f307bf3ce4f4a0779d9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d2d577f7a0f5fe476e4956889f54e6ccb9b849f710f4cf700dd7f060f4e4f23c.npz",
      "sha256": "d0ec2a32db6d30de8b0a525fc0aadfd09c325263fa615c08cc4134938425cb55",
      "shape": [
        256
      ],
      "stored_coordinates": 249
    },
    "language_model.model.layers.6.self_attn.q_norm.weight": {
      "base_sha256": "7e47a125567be4bc3bc46ec958ac2d0e33ac0b17a2051095d3b2f48dcda53714",
      "changed": 253,
      "content_sha256": "4b6824242b6a639613a4d1dbc3ff8c1d870f3804a6150dde6b3d846d7ca46227",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "a2d5a71a7d31a80c81513f8097b59f0d53e8cf1ac6ab541b52ff889db51fa4ff.npz",
      "sha256": "f650442a292be5c45956ad672c158c69f115ffa5badcc59e2f4cadd18335a8aa",
      "shape": [
        256
      ],
      "stored_coordinates": 253
    },
    "language_model.model.layers.7.self_attn.q_norm.weight": {
      "base_sha256": "d889a6d265c731c405bc89a299cf05fddc10680190c4218fd8bb979141d0efe7",
      "changed": 255,
      "content_sha256": "a6b04ddc7f095ac585a54bc10db4ead267645e28950dfaa00a4322424e52ac4a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "a8c03854be343f1a56f1e4489cf255e06314bb1a1aae2516ca482f0f0e4ec6df.npz",
      "sha256": "e6ea1569da58a4661e92164a28382a55f7b4b326ef6e6e683fea8be43bdabaa1",
      "shape": [
        256
      ],
      "stored_coordinates": 255
    },
    "language_model.model.layers.8.self_attn.q_norm.weight": {
      "base_sha256": "00b1c8cf65281b98812522a5daf583bb9c6657be4e9b74ea15997d7abde6bdd4",
      "changed": 253,
      "content_sha256": "67552dcb19c1dcfb708e4bf0361bbda90fe3886f9393404dc1734a2a585cf765",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "08712d60469e0e5600c211d55d831343705b0e279af27f4c133fe592f5aca38b.npz",
      "sha256": "eebe56655a3ce88a44f71b658e094ebcaf364b7aebebb4d95546aa7916e639f2",
      "shape": [
        256
      ],
      "stored_coordinates": 253
    },
    "language_model.model.layers.9.self_attn.q_norm.weight": {
      "base_sha256": "a9c4efebb989e834d80704edcf5ba0392d729f5f4481362927716cf33fb97125",
      "changed": 250,
      "content_sha256": "ed4e1a781261dbea941f8609d5c916a9bfd2f01cd04cef87990e12aac8d2c1bc",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "f4855499d40919174731fa081408f83e7ed088b1d44d397a661727fb1c6d659f.npz",
      "sha256": "fc7239c62884be4b7b6931f34ec80d39d8e82bdd2da7ffa711508ee030204577",
      "shape": [
        256
      ],
      "stored_coordinates": 250
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-ef778263c3970443f9249d3c42a6c2c502adae7d10e1ad6151c04e5453bf039c",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4202586206896552,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 27,
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
        "correct": 18,
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
        "correct": 39,
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

## 第5轮

**当时目的与操作理由（原文）**

Candidate 5: independently reduce all 34 decoder feed-forward residual gains to 0.95 using post_feedforward_layernorm w'=0.95*(1+w0)-1. Tests attention/feed-forward balance after image-gain and query-concentration edits failed. No training, label fitting, or presumed defective layer.

**本轮原记录的主分数**：`0.1206896551724138`；保留原始0–1尺度。

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
  "changed_scalars": 86975,
  "id": "c-4e86bfe7ee2997b6e9df00db25976bc9da4c1d1add6c94aaff1890719f4fd7a6",
  "l2": 1345.7420940206032,
  "parent": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "rationale": "Candidate 5: independently reduce all 34 decoder feed-forward residual gains to 0.95 using post_feedforward_layernorm w'=0.95*(1+w0)-1. Tests attention/feed-forward balance after image-gain and query-concentration edits failed. No training, label fitting, or presumed defective layer.",
  "tensors": {
    "language_model.model.layers.0.post_feedforward_layernorm.weight": {
      "base_sha256": "4d1ae452b9efcb6e878416337ad5ea9bb74f5128109ba117b1efde7f38c0589e",
      "changed": 2541,
      "content_sha256": "7fae7414df391b2b64fbaaf74dc2337ee45df245c9dd7f5b416bd9ca143a4c6a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "5ba727d69136394583fd603b63395a05540ff515454522e9fad8fff136e9ab77.npz",
      "sha256": "58b9baa4afaf9f0f1e4f6204a7ca87376a41d0a185902c94b96f5596ce043f33",
      "shape": [
        2560
      ],
      "stored_coordinates": 2541
    },
    "language_model.model.layers.1.post_feedforward_layernorm.weight": {
      "base_sha256": "34d9e47dcac71d0fad930e7d9e0955af667b643dc3a866c5970ce36d10a4e214",
      "changed": 2555,
      "content_sha256": "942b799212c271195c254850edd4747591e706585db58e0cf19f769d3ca820d9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "3043785de03184f7d69b59c2bbae1def7875c5f86e5ec79bc04560a7e52fac8c.npz",
      "sha256": "b4ea35c9a3242fd37adfecdb18c00e4392312ae30b180ddee3c8a8cc754990c8",
      "shape": [
        2560
      ],
      "stored_coordinates": 2555
    },
    "language_model.model.layers.10.post_feedforward_layernorm.weight": {
      "base_sha256": "af7761db8fb6d65d7a92deced7aa6ed9ab39d59ee3f31efbf19eff7359129043",
      "changed": 2558,
      "content_sha256": "5038f9a587242cbc7a2b5eb26798ab32a279c5a591659fba9199736132abe7b4",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "72f7688908dd4021f31f16b0ab7bcd5e283e44fbb3079a8c543be98fec663b29.npz",
      "sha256": "84ec358208526d058a706a04ffa4ffa79bc47792f561a4104a9048b450772bc7",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.11.post_feedforward_layernorm.weight": {
      "base_sha256": "89d384f0b663a59798d0caf3817acf749d1286ee7fa658a800e45949f2bf9d2c",
      "changed": 2560,
      "content_sha256": "a16109a791c2c847dc4cc3fb665e303506fd04ec5dae48b09aff86cdc61b58da",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "33d2fe715bbaf79c665524c2c134192d6c81f83225430f58ac440f64aea9d0a6.npz",
      "sha256": "131622d70ce97f6a410d75de167708d77f7f5b0af89c961c1c6ace6756b0c849",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.12.post_feedforward_layernorm.weight": {
      "base_sha256": "f04a87a55283cc720a8ed1ea93c3ea3e3998176474beb56db26e85dcdd82fbee",
      "changed": 2559,
      "content_sha256": "456251e025f489db9865285576ec0566920ceb240e1fdd47439aecfbda0ad85e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "364856f727b13766a6dfe092412499e3804b1779e79a98d5d17f571f785f01b0.npz",
      "sha256": "e2e3d2534b50eb95c1fac0e4281f2bdd96d4d7c1763d6159e6951173bed2bea3",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.13.post_feedforward_layernorm.weight": {
      "base_sha256": "f595e44e15f2081870bdfabfe3cd8aef4c5e22bc5f0000b595d59e401df29de3",
      "changed": 2560,
      "content_sha256": "72b26e9a36caa2c888acf2a4ba9843427e8ec331a59fa3aa60e56dc7a9e24ea9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "55908453b2eaf90446af4573a8423cf9ca877947369821efec861e6d5152b13f.npz",
      "sha256": "9c884af56b2cc268dc7ce784cac0f86c437878f8abdfcac7069cda494f765bbd",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.14.post_feedforward_layernorm.weight": {
      "base_sha256": "f4ab4a625f4d59c621557cf3f253fbf7c265bf356d1dd97604a6544d49895af5",
      "changed": 2558,
      "content_sha256": "9818114d76fe34d92bf48d16d7580ac8c57d7d783e4596bc449a317c2852b9c6",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0ff4502ecd17ade201c3be3ba5bd899c24748fe17975d199c57a4d29ad1beae8.npz",
      "sha256": "4600e76b896facdf7a1aa6dcd577d3285743d5bbb608b600084ba700bb5144c2",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.15.post_feedforward_layernorm.weight": {
      "base_sha256": "c3a0ecc631fc86eeaa78e7d6351f2659cebf1132b856183277b448f8db983d4f",
      "changed": 2560,
      "content_sha256": "31744fa4969bca08f33f0116e0b170036df0fed521df6b34e9b7c10f56098983",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "bee0d6867067a9e42d89014f4d3d7bb008f720190fdd6f0d9ba6bc41cdd817c5.npz",
      "sha256": "3c87acab300cdd521b1c55716e32bc53d27aeaa02eba0bfae9099ea6104521f0",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.16.post_feedforward_layernorm.weight": {
      "base_sha256": "83b002dc6701177b1aa90dac5d981fe3cf205a63210de97a2759e071b22afa99",
      "changed": 2560,
      "content_sha256": "10c63388f77e6a83b723cd93402bf1cc82078b00c2ccd451cc5eedd6f7906bee",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ccc477cd6b70843cc0218c101088bfdab11a1f3af23336a1df20fae85f1c8c6e.npz",
      "sha256": "27eac3b22222213a02e257f2051cbc37b3b45684e52f57e6a752376943d297bf",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.17.post_feedforward_layernorm.weight": {
      "base_sha256": "909c707fd7898fe36b26ffdc0e92d398396ffb50c4872e5f9744236bf6ff5cf5",
      "changed": 2559,
      "content_sha256": "8e14a425f082298169779d40cc4a1a21eeccc3ebb3ebc6225c6d44d16ab42499",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d8b3d19f20e2571c310c49349cbb35a2c53b9ed9c8b5d30402480fade61e834e.npz",
      "sha256": "00a3746362a9fb6c304a6c6e8bb06f16e91df1bfb8f2051521e46405de394d55",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.18.post_feedforward_layernorm.weight": {
      "base_sha256": "3c327b7611f24a32db3b90b669bd356334cfdf090ee8764270740d7508343ab1",
      "changed": 2560,
      "content_sha256": "4997f9c9d26f45c67efe15eb4aa0a14a06109428dd5a0b9eb44139e2304ec7f3",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "8ed52067aa07c8b327c623b80134363abfd6a81df9d14180f5bc7b91eec6fbae.npz",
      "sha256": "c85c68eefb38170f3fbda68f50c33d714a549d61af034dfc24e73dd1802efe05",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.19.post_feedforward_layernorm.weight": {
      "base_sha256": "75e2c5e42d4281a971e80deda155f315db6255451a85e89d3f54ee596a941348",
      "changed": 2560,
      "content_sha256": "04518dc9ba49fb75dc8943e599a569053b415efebdc1b735838cae126f829da9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "3068acd71bc65d5ccee8aa09feca75616b331b4c2253cc6f39ba58bf782c1c2e.npz",
      "sha256": "aa85be5b4ed12f5924ccf0bad3c8d5a292360e2c6065699b9944cd6dea31bdae",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.2.post_feedforward_layernorm.weight": {
      "base_sha256": "7ba23c6e074a7d6013a6fe21970c0cc9361ed49862e1683934b065042963081d",
      "changed": 2554,
      "content_sha256": "131af3527604f43bc5f23879bfda166deaa52753dc24b7392d01f1a3cf356ca9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d19217b9d6f7f301cc24a4416125918507b5732edcfe54fa1bb83d498316c4ad.npz",
      "sha256": "5af4c5bc01b75ecb83be0d3d8e5f81f4805cdf44927b5824a892c1eeb1c26e49",
      "shape": [
        2560
      ],
      "stored_coordinates": 2554
    },
    "language_model.model.layers.20.post_feedforward_layernorm.weight": {
      "base_sha256": "ea4337780feb9cf656408c00a4c19fd4e030dc9e8603c6133ae604bd4c6182c7",
      "changed": 2559,
      "content_sha256": "7c1beac2071065170d134789d392223a04ff4c0d1a12520d6969fc1b4d4fb7cf",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "be40af36f5e417b31fa9c0471fd7149391688a81381abf90817dfe4cc9294e71.npz",
      "sha256": "9f95ee8f4e452e9ddb88fbe5d7649b76ab42933b10217c516d88f82d8870963e",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.21.post_feedforward_layernorm.weight": {
      "base_sha256": "cbdc7a1f8b9a39fa3ae80c6e4d3afda42f54b3546f260838ffdc7043af8dee52",
      "changed": 2560,
      "content_sha256": "9eddcfe1a62b3044f0c2701d592ce5007289ed5c971965e03586d92140e8b768",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "f8592e6c92b4d4951711f65302256615871212292c857b97d8416b52855d3c8a.npz",
      "sha256": "8bf6ba9098fdd8e2fa85a8b6cc1de958f15a5e1a81639dfeaa3f380a6d4059e8",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.22.post_feedforward_layernorm.weight": {
      "base_sha256": "7efbd4f118b8c50bb05627be77c5b4e7b65fb5b01e1771397497adb07087a29f",
      "changed": 2559,
      "content_sha256": "97d2bbe8ef931a068c0855fc216656df2552f20746703e3ba777e462a08c69b7",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9b59f2432e6e5ff909e104077ee8b7bffba0d31a2c125d70280eb9f7aba4eab7.npz",
      "sha256": "ab4154df66e5705c7303ae055c6d18b6e44b10de88efde964b35d1e1982203c5",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.23.post_feedforward_layernorm.weight": {
      "base_sha256": "21cb1dcda168867e6ec841a27b8904b023b9e16b0ffef21d5aa5ae8083e17cf6",
      "changed": 2559,
      "content_sha256": "689b6ee7e9ea99b91d91cebb247444293af38eebe916aa246d991dd47a8020ce",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "57c66c318a5615f8a519c12b40043d971e39b8b236dcdbf035ba937cb04a6aca.npz",
      "sha256": "03cefa14e8f9563ee40f5d95f426a233fcc909451073832c341388d4391a9fdd",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.24.post_feedforward_layernorm.weight": {
      "base_sha256": "f90c30e774400f0a9eebd22d9220c281cde9db95366069119c4d09de860b0237",
      "changed": 2560,
      "content_sha256": "a05948df6f45fd0f643b2588198034d6fadb1e11cd62eda4f0a4aa0a8bae47e8",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0b1d6a382a000d64a01657b474a1e957b25748778db048ee42b59031e7693cd1.npz",
      "sha256": "8c9a303f3497c4230d2807b4b3c4ab07884e27053b348e5ed8409b077be5bc7b",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.25.post_feedforward_layernorm.weight": {
      "base_sha256": "aaeebabe1fa818fe3388ded46efca3b2fcfe87049a70d1285411b23092793000",
      "changed": 2560,
      "content_sha256": "1484c9f94e262c9f6ec626108080f3d876b97610d42d24dcbe5bb1f7ec53b5b2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "574a6b7ff84afdfdcfe2f010f66f879e6f9c8dc040987c39b43a0f3efada7203.npz",
      "sha256": "49c393a3ba23efe40021ff59492447a7e83abf64608f353692fbcb2f2d020c90",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.26.post_feedforward_layernorm.weight": {
      "base_sha256": "cd1d93d680e66e0c5649f4079d22f6afaca373da9d4f0df0c981b9e2273196aa",
      "changed": 2560,
      "content_sha256": "5d35982243694506883f5a2b5a88a5e0bc0462258a6f5c334069a49a4e6a82f4",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "af4c62bf12cd54912be9139e6e3992ff89db2aa89b3893fac489c2fbf1ceb48e.npz",
      "sha256": "01b306f95dfbd059f34baa5ebf2a6ed2f5185fefbc125c35dcd4a28d952aff49",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.27.post_feedforward_layernorm.weight": {
      "base_sha256": "0a0191055a177497217a5301b209bf912d04361bf09fcc934686406671142058",
      "changed": 2560,
      "content_sha256": "ad900c1e66baf2a124ef1b9cd084afc0a70b24025369eacf8fbd59a78677be69",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c01d30cf50acff3982f1344d5b19830e6021a1be84945b613a0e770a2783d9cd.npz",
      "sha256": "d1bf1394a7f6b101fe6e41d8d264ac9a411c959d8ea32eb160cbee24b76fc18d",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.28.post_feedforward_layernorm.weight": {
      "base_sha256": "5db6d15e40b990711ed9aa0552a195bd76eed7c5074cab2737ab13a8846e5038",
      "changed": 2560,
      "content_sha256": "3573fa9ffb11ee7e4c9480b782a7de4343580693431eb1016e549282fb1b750b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9d7633e008ec94a56b6423be08fb87a8a04b57f4b061b97206d1a032ca1429a8.npz",
      "sha256": "1977049286f93596af2e753de62d2975af34ee86ea292c3bd609feb210237ebb",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.29.post_feedforward_layernorm.weight": {
      "base_sha256": "3c9b3122d708a2d60b44c233d10998d8e7b7c7ac6ea38cd836d7316ba2fd8972",
      "changed": 2560,
      "content_sha256": "08e0620c8fd33f8a01a974348f48e0e9b105ebff2dbaa31ba957a261be7b072f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "fa92473f5909de0227e5424a048e4bae0f313ba4a902991b75b39057753da0dd.npz",
      "sha256": "082e1264dae6e1ee01287d8d194e13cc58ff26fc315bda7b95fc669da6ffe6a5",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.3.post_feedforward_layernorm.weight": {
      "base_sha256": "7cabe9ab9a7858d9c3e94a3e8f66b9f9b94007ab11007c63e2ff7263c5b74383",
      "changed": 2549,
      "content_sha256": "4bfbada462a3142f22753e4df0a0d9abd66469c3d87beb748ee6843aebe4fedb",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "615261243226abac034054cbbf923da84686df97447bfdd44e26734596fa4258.npz",
      "sha256": "37e1b3909e18acfc6a4ebef356cdfd581a19bc420502ec1ccd0d05b87bc83a21",
      "shape": [
        2560
      ],
      "stored_coordinates": 2549
    },
    "language_model.model.layers.30.post_feedforward_layernorm.weight": {
      "base_sha256": "3b1038978f803988e5e6de2d5ddb2e696cbe84558b39f8645405a7bfa1ee50f3",
      "changed": 2560,
      "content_sha256": "d430e11aa0f0d19ef657ed10344b478c83fb28f351dd9e9134418c8cda031656",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c7195d7bbbf3ec90680d4cd156699f0ad9b611d9ddfc78b684046d1f6dc21c84.npz",
      "sha256": "9f95fc5892076c859a09937d5309d577f4daa13c3c2c0bb80693ab7518b97238",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.31.post_feedforward_layernorm.weight": {
      "base_sha256": "25e5d11534379bcf874a73d739c8c47d4077ad2e66cac4ac99e0891bb1758f15",
      "changed": 2560,
      "content_sha256": "9fdc399b445351fc291a1b503e4a50eb8610198512fe3eac9d9a612826272984",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "822f1a8b17a51a9a82e221e664c005431e34783377660f9afbd7d10e0ef96992.npz",
      "sha256": "21eeea973ef887c552be2d14d70daeec1089d4b1d68a3d6a189673c9484ef29b",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.32.post_feedforward_layernorm.weight": {
      "base_sha256": "1f490a1004857564bd05c5a631b0b5a6b40b7564042225a9a8ec65e1992e4476",
      "changed": 2560,
      "content_sha256": "1e2ab2489e8650c29a3836cd64a8a83e70af2c8fb2ddb6d90e81c11c93fe239f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "034e0acb9ca8b3bda13b3312468db3d84010807a503c4f61341b0d469032c067.npz",
      "sha256": "2746b2f984815e67aabab48c28ea27496d90441be6c810905684437c96e3a243",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 2560,
      "content_sha256": "3a8968ab66941b8213b6c37cbdb39179063fb0d350877147b314cac6a93bea4e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "402bcd5884f11dbd34ff76ab6f2249dd8ba1203b06962511ae812e4a0c0e8f5c",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.4.post_feedforward_layernorm.weight": {
      "base_sha256": "0cbd169db1d4ae9e2c5cd546dae9fe997448c2af2f9ac682c0a368db8274a934",
      "changed": 2557,
      "content_sha256": "80b8a6704b5cbee6bcf7939bae416ae1c6e8916ae846c6398b00432bf408dc06",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "47402777e17d78ecc6523e21c921b515e730fc00545f0b66ba6465423c9c1de8.npz",
      "sha256": "3c3872c46e1149fcef66ba6861e479cd0c3999e390c8fcc698e4e67af99de993",
      "shape": [
        2560
      ],
      "stored_coordinates": 2557
    },
    "language_model.model.layers.5.post_feedforward_layernorm.weight": {
      "base_sha256": "50d2b10526e4e98e53be4e791087ccf1b8f00b14065981a8480d4707705eab85",
      "changed": 2556,
      "content_sha256": "d3e0a012519aaf58ceea3d272cfb727f720c7b2b23bc35f5be1e0aadcd11cb71",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "721cf796c77ca19da54e1fadac9a960f3b191367320b198173d870a75e9fccf6.npz",
      "sha256": "f6bde6088b75f3725e355959b59b01bc85b236773c1e81ccc93a3c0503ac20b5",
      "shape": [
        2560
      ],
      "stored_coordinates": 2556
    },
    "language_model.model.layers.6.post_feedforward_layernorm.weight": {
      "base_sha256": "7a12e34412b076f6131e31747ab5396751f334b3fd00192be608f83e9db86051",
      "changed": 2558,
      "content_sha256": "cfd84de9e4d753b7b07e221d545e651d860933dee0c4a0f09c99f5670bf33628",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "5dc5b2fd489c100c79bb238ad3b2e65e26153847eaf5c19b10bd8b413992d67e.npz",
      "sha256": "6a9b3c93201075c0237807c37ef2c5d4af51a11e91b83378e8969084f319e819",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.7.post_feedforward_layernorm.weight": {
      "base_sha256": "4047ab8dd31dc5fe079ad664f9e9b9d1b224ede91a5bd71432cc6e1343d5ca86",
      "changed": 2558,
      "content_sha256": "e9f2be85d0d299814c7b91a40058b09a544826c0d0e96c50600493bde17edd32",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b2542d99a990ca2076dceec5b257ba9f32acb35aa0b4e4f45ff206dcb6313e49.npz",
      "sha256": "c15780e8c916ee0bacb62b610c92e6b72f244169bd57b300cfe5068f352f0d11",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.8.post_feedforward_layernorm.weight": {
      "base_sha256": "b0494c300d1bf8aeb1054b693e119bb4e046b3b1e39b302c9aa51648b4614f46",
      "changed": 2558,
      "content_sha256": "ac24e40679c29a461c9486e2d8a7b45070c4e79dc86e3434f55271bb714dff84",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4fdd0090a05f653dbc385da916a94c0f8e60b6fef947c4dcf6aaa8d6344ac18a.npz",
      "sha256": "ba147d5eb44cb5fbe4cccc50ffcb6475d547c1efca3fd642300a710d5e889b5a",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.9.post_feedforward_layernorm.weight": {
      "base_sha256": "26c6490dfd39ca7b613f8bf76ae4f3afc029c9ff89a1032f0b9f70d19df4980e",
      "changed": 2558,
      "content_sha256": "af3d084e98cee44c34e1c7020249dce28797ebdb85f6fe7dedd2dd578db08671",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0c8e013044212b7472539090ce5481b7e2a763cfcb21d33d800f1e92faaf0830.npz",
      "sha256": "62b456589bd34ac23c46598d79e52511091b4589650c8ef0bc1be12a5d9de981",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-4e86bfe7ee2997b6e9df00db25976bc9da4c1d1add6c94aaff1890719f4fd7a6",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.41810344827586204,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 14,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 27,
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
        "correct": 33,
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
    "format_errors": 10,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.10344827586206896,
    "repair_score": 0.1206896551724138,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第6轮

**当时目的与操作理由（原文）**

Candidate 6: restore every feed-forward edit to W0 and set all post_attention_layernorm effective gains to 1.05. Tests attention residual amplitude separately from query concentration and feed-forward suppression. Candidate 5 harmed joint correctness and formatting; this candidate is independently W0-based.

**本轮原记录的主分数**：`0.1206896551724138`；保留原始0–1尺度。

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
  "changed_scalars": 86107,
  "id": "c-7c30a3dde49580784c93970aa49343b012d3079fb22131c866059d7dd08e48f8",
  "l2": 863.2906405290918,
  "parent": "c-4e86bfe7ee2997b6e9df00db25976bc9da4c1d1add6c94aaff1890719f4fd7a6",
  "rationale": "Candidate 6: restore every feed-forward edit to W0 and set all post_attention_layernorm effective gains to 1.05. Tests attention residual amplitude separately from query concentration and feed-forward suppression. Candidate 5 harmed joint correctness and formatting; this candidate is independently W0-based.",
  "tensors": {
    "language_model.model.layers.0.post_attention_layernorm.weight": {
      "base_sha256": "53d94cede36fe89aed217c6c2f629324743464ba8394052754a6dc75d6ac4bef",
      "changed": 2077,
      "content_sha256": "561b68f19f782ff6f794f8d13ee2fdf87a3cf9daee156e486193488daa264269",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "a77f005719dad6d425a413981170d6619aefc36947c70e804b0e1cb23ed747b2.npz",
      "sha256": "e8954b1ef65b619d7c9810c0f590d3abf1030ad91255b24ef76cf3bffc7fa1e9",
      "shape": [
        2560
      ],
      "stored_coordinates": 2077
    },
    "language_model.model.layers.1.post_attention_layernorm.weight": {
      "base_sha256": "3e22bcb473b0ecae1d93fde14cde1e84227e2b211e913150d835ce66a5047399",
      "changed": 2476,
      "content_sha256": "4389dab5ea50a498f74fb3e3aea92d947d64dbd4e9d99928c4be86cfdabe268a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "bcdc10868b8ef17328a818d77525c29499eeee774dcb0741342e7b1339a91399.npz",
      "sha256": "b5f495f09b60745c43fa44f1293989bb6ff140088a86ea4f6cdf3a4628dc0914",
      "shape": [
        2560
      ],
      "stored_coordinates": 2476
    },
    "language_model.model.layers.10.post_attention_layernorm.weight": {
      "base_sha256": "d054981e9a3909e58d35a04f4bda50ac2ead3dabebcf75d98658b537476d194f",
      "changed": 2546,
      "content_sha256": "12f65c215e46f2650357b2360fb21697f0e4a7795edad9915f54475394e7bee0",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "44e0f408e465ffe6495611eef5330ccd23ad7b1ff14090a0687f33ff9a1659b6.npz",
      "sha256": "d9ea970450b0dadf4caa120fee862e21ed058571837bc36f6bddda9d20f56c70",
      "shape": [
        2560
      ],
      "stored_coordinates": 2546
    },
    "language_model.model.layers.11.post_attention_layernorm.weight": {
      "base_sha256": "5696484f555d320e73d6ba86f877ada9781159df5a0944f8f0977b5100e60a3e",
      "changed": 2546,
      "content_sha256": "7ae61268b651c26d98ff3576ebb07de3a78d168a306aaee230956b396d436d59",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d9a43481c8d9604d783a0fdba884a882f55050341a63b6333c21921d798ae174.npz",
      "sha256": "96f5efc84e21a304bef0e711cb8e72d71711a788864f6e5f062c74a02558d821",
      "shape": [
        2560
      ],
      "stored_coordinates": 2546
    },
    "language_model.model.layers.12.post_attention_layernorm.weight": {
      "base_sha256": "be00db50fb24f487a26b6baba4701af7a1c1dd4096c9113875342abc0a0d8346",
      "changed": 2525,
      "content_sha256": "3d8e7dea17cb3e859518a45be2b6903f6bf42420b09b857fb6091725e3a6d387",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "153280aa8d04587f09541c8ed731b16aa07189e343d0f2154fc1078bdb82eb53.npz",
      "sha256": "0bbef8fbd07b53033bbdc49976a5cfa5011936a4867625d049fc97933a946e37",
      "shape": [
        2560
      ],
      "stored_coordinates": 2525
    },
    "language_model.model.layers.13.post_attention_layernorm.weight": {
      "base_sha256": "ca12c7dedab9a7d241fe5e657d586d50485daf6dcd8fb3aa466adb18a38f0514",
      "changed": 2559,
      "content_sha256": "8f0770d645ad4d6252a82c81366af01d401b020460d6e2ec688f353c6492f194",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b6d7f81cecd99215c788058f3f3995bb2d12558821784b7622c7138010134a0d.npz",
      "sha256": "0f2aa947fa07bf510e0bfe0208ba71710990874ddb135da03af6b2e17b57af64",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.14.post_attention_layernorm.weight": {
      "base_sha256": "4651834d1149ea7116fad91a61cab71a76f32c234a7d6a99375b5a062c8f915a",
      "changed": 2536,
      "content_sha256": "14d05cc577f15416037f9b46182a7041487258b981ade570757329742d3ba449",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7ea7969fd5f1ab4c4ace75e7ea646b93f78a4aa4ec3f195a5f02a69e19344277.npz",
      "sha256": "e149cfaf8024aab78481e822817cfa515cf40914c98466a95b268a4c1d8b82ca",
      "shape": [
        2560
      ],
      "stored_coordinates": 2536
    },
    "language_model.model.layers.15.post_attention_layernorm.weight": {
      "base_sha256": "e89d0d63fd097bdedb1aa1dbf2a13ed85c1514c300737af3ce9702da4cdfd515",
      "changed": 2542,
      "content_sha256": "42b0a889fdc9db48ebfdabd7cc8cf522b4dd6afe133f185bd9b205157b61836b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "cdd2afaa265a46b79b32fc239f8e11b39b7c61ea2419109f7fdf9dd5b3009207.npz",
      "sha256": "ef3be88855de74094ce7e5c917d6f59d358ddf46cfd992037853a80bff63263a",
      "shape": [
        2560
      ],
      "stored_coordinates": 2542
    },
    "language_model.model.layers.16.post_attention_layernorm.weight": {
      "base_sha256": "8f1ab8b0f2e0a29ef36fda64e3359ecf94d3e3be08b26b86c45a5213081f3cc7",
      "changed": 2552,
      "content_sha256": "db757eea8371246749ad4361633968783a98f67c80fca0d0360c2ae857746b35",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "e8e4f005c19810ef333e55af5ed90b1e278c2d20574a86ea45e41b733bdadbc7.npz",
      "sha256": "a7ec6d323ec4c103d137a4fa045a63ee82135c85220143c0b53854d48c260eaa",
      "shape": [
        2560
      ],
      "stored_coordinates": 2552
    },
    "language_model.model.layers.17.post_attention_layernorm.weight": {
      "base_sha256": "803151ba6f589e26d756a6bd15fd8a036dc7ebbc35212e174f45aa756d9f3c1d",
      "changed": 2557,
      "content_sha256": "e3e4cee1e3880ac18c9109c694c4d9a2bd76275e342f3f6875b889278837c2d1",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "916e8b8e25eaf1cbcee9430038dbb79cf6df7f4ea6770b9f985c20ef9804d3ce.npz",
      "sha256": "7c3c2f95f036726009af54f77b79dc67a0589c847cf0847ce0ee858ab11365a6",
      "shape": [
        2560
      ],
      "stored_coordinates": 2557
    },
    "language_model.model.layers.18.post_attention_layernorm.weight": {
      "base_sha256": "916004f43c817e02e48f26b8f0667de27e862f4c129d1859281b6f2c7a64face",
      "changed": 2548,
      "content_sha256": "207372b157fe4fd5a03e63783b98c18b273433244cd7c9e2008c97070662caaa",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "25ed5483205611702afbc460b79169a115f17956ca0b8d69eec559b8dfa20822.npz",
      "sha256": "d0bbcaa1aa181049cc3cec86edb9b02694b5e0f3d327011a3ddf59a03ef05165",
      "shape": [
        2560
      ],
      "stored_coordinates": 2548
    },
    "language_model.model.layers.19.post_attention_layernorm.weight": {
      "base_sha256": "f1a80d33d927b8a8fceea41aa1944ff52af6520c5e81bd6a347c5f1d38660d8e",
      "changed": 2551,
      "content_sha256": "be820752eb629913ed9fa29a39f123ac25b8ea3184b5aa60da1eb29a1836a3e3",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "421a394db2609c35899edce702ab39dc86b39204f3150c4dd5bf86c9c7b9c034.npz",
      "sha256": "ae1b9ad990c95783c2fbc5a7d40149dc393718317baebe5ff62de024160a3701",
      "shape": [
        2560
      ],
      "stored_coordinates": 2551
    },
    "language_model.model.layers.2.post_attention_layernorm.weight": {
      "base_sha256": "ed9281bdc2c5432cfae383b2d23f87c786952c275060323a3e65865930b4df12",
      "changed": 2504,
      "content_sha256": "97313a5f686976bd0e7855bf064295443a6583b5e58dbbab64dffb7d5f0ce5bf",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "69c7bdf2f4c873274f24a08c21dabf23e5a9868d6e3d6d6294531f3f95ab05aa.npz",
      "sha256": "264b89e2edb5e524f3af86db83b032acf2005d398b98c372a663e93371261b8a",
      "shape": [
        2560
      ],
      "stored_coordinates": 2504
    },
    "language_model.model.layers.20.post_attention_layernorm.weight": {
      "base_sha256": "37d43b8fe8806c7b65f16ed23fb31da5c03e92809439edec6a67cc36fef36cf8",
      "changed": 2553,
      "content_sha256": "8097f76afd65960ede02e832afdacb2cd23f76e73523587849e2b1ad37106a02",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "56d24b947f92935bf35acfba4eed7da061e82e0388529b0808899be2747c2e0f.npz",
      "sha256": "f63662f567d828850ce7945723db13b653d82d42cffc47e864587963c9b5b9d7",
      "shape": [
        2560
      ],
      "stored_coordinates": 2553
    },
    "language_model.model.layers.21.post_attention_layernorm.weight": {
      "base_sha256": "ecf77d197405867dd66c81b67e21928dec89f220f6fb4d1e83307717650d73ed",
      "changed": 2558,
      "content_sha256": "343886e47f569c01f971f754970331ba937acf031ae79b2aa09d956b1f916325",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "a7710d8cc61889ac1d754088355702d50ce867ecaa719b0a5d9629c40a22f5fc.npz",
      "sha256": "665acd66798623cb0bc95f25a4fe217801f5767cf0683f8eb02c399f41fd7f9a",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.22.post_attention_layernorm.weight": {
      "base_sha256": "e438e6b262b68709c8e715febf443e809d4d7b7e0f0321026e86fd1a8a736c08",
      "changed": 2555,
      "content_sha256": "dbec32a0f7f6e0856b7d9d159f479ab298e2c86f7d35fcffaa94bc00fc2dd3c1",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c4b6075ed6bf96b1a85c342e3bb4aaa1dbab78ff18940fc2f0a305456d5a8aab.npz",
      "sha256": "113323372cd968a4103be65caaf49635ce5c6e1b15dfd2674f61dd1dbe097879",
      "shape": [
        2560
      ],
      "stored_coordinates": 2555
    },
    "language_model.model.layers.23.post_attention_layernorm.weight": {
      "base_sha256": "cae8c662a24ed17bbc323f3ceb20df4342139bbc724ea2e07174bd04681ab965",
      "changed": 2559,
      "content_sha256": "0fcb7c115f1cdabddc514d509d91f504415aa6e38fbd8ff9ad99d466ef2c01a1",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ae549643feded92676d56843c6fda4f7d18694e70e4e81059d68b857a742d331.npz",
      "sha256": "9e1181dadc89288356a27200addde25e1e1bbbb5b68ff593792662a2b23b5bfc",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.24.post_attention_layernorm.weight": {
      "base_sha256": "5e264fcb54311d8adc92a04fcd41900703dcfe7596288e738e8e8cf94fefc7fe",
      "changed": 2559,
      "content_sha256": "1730b2cca0b7fdd8447077984beb85ee3c95f25d6637430d4581b131f484cef2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "3e2a774e069b274c4e65f77f4649bce59b9516c4825acd479efb3e59a3b6addb.npz",
      "sha256": "e73e827d3a37324a3703ccba3d2d3eab16aa4fc4772ee10e960701972d1de8d7",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.25.post_attention_layernorm.weight": {
      "base_sha256": "6318814e677e136b4763ca87fb583311e6f59321ba82d24c57f65e57688d6785",
      "changed": 2560,
      "content_sha256": "b20cbae61ec104e9a36237b2e8d820fe69896d2bad0867de2fed39f34ac7e4bc",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "1bdfa08873daf3a0b4ac8ea8f267241fff359623fb05d0c2a5156ec1a320c36f.npz",
      "sha256": "1f6aef843f7febd553cb06851d40b6dabff0a9cc364bb48fcc00c30a4da46c27",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.26.post_attention_layernorm.weight": {
      "base_sha256": "932efdf65ef698d03de6debddf59f24874a1595c77c3edf87a029dd3175c4ad5",
      "changed": 2559,
      "content_sha256": "eae3af5229619c8ca26570b148e0cd14fcf70bc998573d2b3fe5148b4433b09e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "77086caef1f7fdf9e67880748ec0ed0e6719785fa853224bce10a99074222b54.npz",
      "sha256": "8abe4609e741119a994e73812860165032e18f898d0481715a844e5449250987",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.27.post_attention_layernorm.weight": {
      "base_sha256": "5b7b766c4fecaa3af0599d09cd942ec9150a8b700d34649b884b0967f25e2387",
      "changed": 2560,
      "content_sha256": "10fe8b2d6a930335024565ac171fcdd5e19cf296d4787a39504d12314cd16b58",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c57181aed55878f2b32de1ae68b53ab5f4553f808658bb7fb7f1239d062980f4.npz",
      "sha256": "3a03f5fb0fb2996d3e580526079f843b32bc9f78fc41cb185c1c9529676f1237",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.28.post_attention_layernorm.weight": {
      "base_sha256": "d8dfc712698540d6951844fc2d3715f1a97fb7fced831649f384a238a16e3832",
      "changed": 2560,
      "content_sha256": "d9f138ff49040aec01766feec3a2eb490abb1546d50e86e23de427a520d35874",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7e4c6f13a000c9db06f01e7e846ef56b712cda7e9038c0d1205ee2ad1260a19e.npz",
      "sha256": "c49f8e5edfbcbc52e46023e335a764ece3a750668010cff16b894b2f39cac44e",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.29.post_attention_layernorm.weight": {
      "base_sha256": "c2f6544e0d961568c20d6acf6a08d69ef732e67a08414264cf7a22d533168943",
      "changed": 2558,
      "content_sha256": "021254e4c3a2ae5b037a3f4e03a1b236529eba734649dadfd4e4b67831338608",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "da7cd558ac798101726155e7974aad934f5a5d360a285b6fcd7c47dd955a40b5.npz",
      "sha256": "f416c21da79d6004a081483bd64309b50a72e9e90a2e6d03befff473b29b2719",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.3.post_attention_layernorm.weight": {
      "base_sha256": "37b3d36eb7d61af802a12a4c064186b15ca10ab12469b33c9775f3a6d813b1f1",
      "changed": 2552,
      "content_sha256": "b0f30f42802a49ddebdc53bf4d3689301828ed8e2e86b6206ccf3287b3c6382a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "deeaacc8314911f7d80d39e122347e77e30633d0941d5df20b1aaf4ed3dc615b.npz",
      "sha256": "6af2d8f25998c2ba123024b4b39a9db2ecda1b66edc339b965335f51180aaad9",
      "shape": [
        2560
      ],
      "stored_coordinates": 2552
    },
    "language_model.model.layers.30.post_attention_layernorm.weight": {
      "base_sha256": "e0943a6f0643e2664491a1ec50f1f2850738bfcc99f45c0775645b14c6b3ea11",
      "changed": 2560,
      "content_sha256": "15f855d29ca79c69e252d99dfa6615797ee167fa4ff608e1105d4f9565d7ad8d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "011c62170f811e20610cffa220f4205d4ed1da27ce2a11c03d629391a38e64c0.npz",
      "sha256": "ddfc9dbc6ffd5bb47791f97082905382d3c00c200496eceb61ec61afe5df99e4",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.31.post_attention_layernorm.weight": {
      "base_sha256": "925b5564431e6b26598995d6edc0cf2b2cf9d8b9b883cb22201dd7c572e59850",
      "changed": 2559,
      "content_sha256": "0cd875e2e9bb0d65f305bdbaa45acc06bc48da486041dcc8cd7218de151de399",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7bad0c49d4a37332d9e69fcec6c7b2f1945b1eabb11e482de0dcb6ed5eca965c.npz",
      "sha256": "29a1f53fd80491b79287b3ae60a022f3bfb9f08f0d89edf1be8b7e18346024bb",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.32.post_attention_layernorm.weight": {
      "base_sha256": "a04b1dc858c775c5042fb8ad6c5a0438ef784fc8dac40e72e15f5900a0758688",
      "changed": 2560,
      "content_sha256": "cc2bd32fd5df92f2049efc38865d516edeef38a314b60fb406744dda89aa7443",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "98c92d72de663bbf335913c29c73230a435fd3d5da3292588f02a9f387166da0.npz",
      "sha256": "56d4cc3e1b3f26bd139e1ebb4b825e21cd0b780964cce0b9dd7e2b2766f24138",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.33.post_attention_layernorm.weight": {
      "base_sha256": "3fb756cb8c482f940baeb49ec47ae21d2b612ae83fe4f1bbdf8ca566b35d126e",
      "changed": 2559,
      "content_sha256": "b8486066fa5ae2520e06e9c712d220cce0bf04a7cba11f2edcc54e28074e299e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "29323b0704970fa1e660f1405f812417f1c293aa7a7433c972338661a92e213a.npz",
      "sha256": "36355a5b81d8bfe98cee0ec8755ecd13b3280ea9865186ec555594ba7b33fcef",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.4.post_attention_layernorm.weight": {
      "base_sha256": "a205e703219f2894aa0debbde39583c857d97b2b71a9c9a266fc367de64f489d",
      "changed": 2534,
      "content_sha256": "16314576069d7cfdb79d11d5d8d1cb14de3608a51d3f0d2633fe0422466471ce",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b2d750b44cb392f5a09dd6fa4771350af7c2d00fe7dd8511204d12373edc4bce.npz",
      "sha256": "229b76261526874b3245313774e73301a972cab1b9e95073b83501a2899dd6f9",
      "shape": [
        2560
      ],
      "stored_coordinates": 2534
    },
    "language_model.model.layers.5.post_attention_layernorm.weight": {
      "base_sha256": "ad676442ed1551aea51af6bff08ce55594cd57d5fa2dbee76c884a98b0b7253a",
      "changed": 2549,
      "content_sha256": "f6cd7c46200661c22bc3b9612fe3e113b0c2b0bf1ed20b955e4da1b0bca808f9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "45828bb9a9383ccdaff413a4eb26f7250a9ad43efc7720b351f01ef5fc4034f7.npz",
      "sha256": "2d3573e4d13a59bbc0a798a19c0c66cd763466cf6830fefd3edd44a337786d47",
      "shape": [
        2560
      ],
      "stored_coordinates": 2549
    },
    "language_model.model.layers.6.post_attention_layernorm.weight": {
      "base_sha256": "d116d4dc1c63b2a4e5dc763b5f26907f5bc7e8ae646373d18752e06b1d503e75",
      "changed": 2513,
      "content_sha256": "171279c4c62dca06926fc6ac647138762a7a4a54602728f7ac1a6fa3bb1cec9c",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "2143c4a4c71ef53ff396ce91d74fbbd89a7d3b2f8190dd7887a62bae4978cc63.npz",
      "sha256": "9aeacf8c9b3931f479d4dd1d5847cb5512a8869b613eb5b7c826b05a8ed5531b",
      "shape": [
        2560
      ],
      "stored_coordinates": 2513
    },
    "language_model.model.layers.7.post_attention_layernorm.weight": {
      "base_sha256": "dd638d0d950e249ce01273d2ab3ddffbcd1a9daad984f6f0b37c54214a4e7c1d",
      "changed": 2542,
      "content_sha256": "7de86aa223811627d7cdde3c8daa72022937cc6c5120c4889a18deaffb0aafe7",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9bcbd8279fbafac857fc232d33351f52941ecd4bbd0c4dbdd1d42248c949cbea.npz",
      "sha256": "1da7822ceeba121dfb90847f84c63c977da9331373e178780265b861582a4df1",
      "shape": [
        2560
      ],
      "stored_coordinates": 2542
    },
    "language_model.model.layers.8.post_attention_layernorm.weight": {
      "base_sha256": "0eaadc2fd18af6eeff6993953e8d846875a69833412c41e7b80fe85f15731afa",
      "changed": 2545,
      "content_sha256": "e5fb9918d2ff8278ec93b6931a41a8f80eb5c088799c556d4d90c8c40bbbbb40",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d140546f150614bb02c51a67da2db32558363aadac4ce29abb47956c86d1615.npz",
      "sha256": "b9eb2f2ffa4861c90ff8076b97ee438cc6bfd4158a54dd613281ec79b47ce476",
      "shape": [
        2560
      ],
      "stored_coordinates": 2545
    },
    "language_model.model.layers.9.post_attention_layernorm.weight": {
      "base_sha256": "714bbce43eb9e0214ff97b76afaff8d14e78bca01268945de4285d0610d8fd1a",
      "changed": 2534,
      "content_sha256": "7d5710dcf9df84180325527fa136bd75e420e69a891b2756c9b725dc0c078f7f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "67183f359385738eb1515a527f09dd7b8a3704eafe00c0fc9adacb077df10b21.npz",
      "sha256": "bb8274f9ee07488c21aeca7f7bb7ada75f60de1ecebb30eb27caad93831be14e",
      "shape": [
        2560
      ],
      "stored_coordinates": 2534
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-7c30a3dde49580784c93970aa49343b012d3079fb22131c866059d7dd08e48f8",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4245689655172414,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 14,
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
        "correct": 17,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
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
    "format_errors": 9,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.10344827586206896,
    "repair_score": 0.1206896551724138,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第7轮

**当时目的与操作理由（原文）**

Candidate 7: restore attention output norms to W0 and increase all decoder post_feedforward_layernorm effective gains to 1.05. Both interventions favoring attention over feed-forward computation reduced joint correctness to 0.12069; test the opposite balance, with no training or fitted neuron ranking.

**本轮原记录的主分数**：`0.1724137931034483`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 86975,
  "id": "c-ca8cbee98860677bf0a75be04d1f27223d5671d856123e1a97e8cbf0a498b80c",
  "l2": 1345.5248882532317,
  "parent": "c-7c30a3dde49580784c93970aa49343b012d3079fb22131c866059d7dd08e48f8",
  "rationale": "Candidate 7: restore attention output norms to W0 and increase all decoder post_feedforward_layernorm effective gains to 1.05. Both interventions favoring attention over feed-forward computation reduced joint correctness to 0.12069; test the opposite balance, with no training or fitted neuron ranking.",
  "tensors": {
    "language_model.model.layers.0.post_feedforward_layernorm.weight": {
      "base_sha256": "4d1ae452b9efcb6e878416337ad5ea9bb74f5128109ba117b1efde7f38c0589e",
      "changed": 2541,
      "content_sha256": "c2fda465a0b609e2f802274e8cae7755f2d76247cda9b470377c93f7bf22d5e2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "5ba727d69136394583fd603b63395a05540ff515454522e9fad8fff136e9ab77.npz",
      "sha256": "2c47013622eb16cd8047d55ee301833f58008a9509257a5f64a7583374a3ba47",
      "shape": [
        2560
      ],
      "stored_coordinates": 2541
    },
    "language_model.model.layers.1.post_feedforward_layernorm.weight": {
      "base_sha256": "34d9e47dcac71d0fad930e7d9e0955af667b643dc3a866c5970ce36d10a4e214",
      "changed": 2555,
      "content_sha256": "92cc8424a3e55d6e98183092e7f32a0c97f1cc904d099e237c89b368a671166d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "3043785de03184f7d69b59c2bbae1def7875c5f86e5ec79bc04560a7e52fac8c.npz",
      "sha256": "97b3cd0255141e99c4f918985dd7598049b93f3cb7bda41506a296afc585e684",
      "shape": [
        2560
      ],
      "stored_coordinates": 2555
    },
    "language_model.model.layers.10.post_feedforward_layernorm.weight": {
      "base_sha256": "af7761db8fb6d65d7a92deced7aa6ed9ab39d59ee3f31efbf19eff7359129043",
      "changed": 2558,
      "content_sha256": "3c9c78b99197609711451c8f1ee458c89162e6f1c8c68c82c5557627997dab24",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "72f7688908dd4021f31f16b0ab7bcd5e283e44fbb3079a8c543be98fec663b29.npz",
      "sha256": "3fc88008768b77665446a2f3d2a44d96fc1c0b4a47d0386903e83268c4ec7fdf",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.11.post_feedforward_layernorm.weight": {
      "base_sha256": "89d384f0b663a59798d0caf3817acf749d1286ee7fa658a800e45949f2bf9d2c",
      "changed": 2560,
      "content_sha256": "a851d956287651329e5de178ad583fcd154c8d2e718debedaa119035f6b60afa",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "33d2fe715bbaf79c665524c2c134192d6c81f83225430f58ac440f64aea9d0a6.npz",
      "sha256": "e8534ce4dc8a324a64f1a55ad54f30e9c62f66dbb8f7bd3562fdb061c4727b8e",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.12.post_feedforward_layernorm.weight": {
      "base_sha256": "f04a87a55283cc720a8ed1ea93c3ea3e3998176474beb56db26e85dcdd82fbee",
      "changed": 2559,
      "content_sha256": "f7f15bd6af8f1b196291e168d550003e25a8972e6bc0e110fa486b59ffa29282",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "364856f727b13766a6dfe092412499e3804b1779e79a98d5d17f571f785f01b0.npz",
      "sha256": "1df1eb0659363725648a2d33ecdb74462bb2a6c3a16851c30a8de2a681260e54",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.13.post_feedforward_layernorm.weight": {
      "base_sha256": "f595e44e15f2081870bdfabfe3cd8aef4c5e22bc5f0000b595d59e401df29de3",
      "changed": 2560,
      "content_sha256": "97c4028df7129f922e8043f4d247714fed4ec469dc92b933c3465b3065f627e0",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "55908453b2eaf90446af4573a8423cf9ca877947369821efec861e6d5152b13f.npz",
      "sha256": "f51f983ddb508b47a9069b3fd4d623226d5c0028a483906fb46dedc42808afca",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.14.post_feedforward_layernorm.weight": {
      "base_sha256": "f4ab4a625f4d59c621557cf3f253fbf7c265bf356d1dd97604a6544d49895af5",
      "changed": 2558,
      "content_sha256": "222771a961a73c37abe15e50bca27428b0f5cfee941736281215c1773c6fcb0d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0ff4502ecd17ade201c3be3ba5bd899c24748fe17975d199c57a4d29ad1beae8.npz",
      "sha256": "ce39d7b2b8f3ba450de2690d54d2bb6dd3d5cda801e1f257295e03297f9be41a",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.15.post_feedforward_layernorm.weight": {
      "base_sha256": "c3a0ecc631fc86eeaa78e7d6351f2659cebf1132b856183277b448f8db983d4f",
      "changed": 2560,
      "content_sha256": "559079360d617d908ffe95118f7444e7030c447ddb753abb4cca983848248054",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "bee0d6867067a9e42d89014f4d3d7bb008f720190fdd6f0d9ba6bc41cdd817c5.npz",
      "sha256": "5af9d3b3e923a19d1b4da8b913cf65d1fb221dd3e0473cf7d13482436bb3fbe6",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.16.post_feedforward_layernorm.weight": {
      "base_sha256": "83b002dc6701177b1aa90dac5d981fe3cf205a63210de97a2759e071b22afa99",
      "changed": 2560,
      "content_sha256": "2cd73ba02bda1008a37bb65d53669f4831067dd37eb1f8005e721875920d40da",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ccc477cd6b70843cc0218c101088bfdab11a1f3af23336a1df20fae85f1c8c6e.npz",
      "sha256": "165ff4c23be74fbd70336546943116757c1565a23e2db49c19a1afe5717a25e4",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.17.post_feedforward_layernorm.weight": {
      "base_sha256": "909c707fd7898fe36b26ffdc0e92d398396ffb50c4872e5f9744236bf6ff5cf5",
      "changed": 2559,
      "content_sha256": "0e7eda7dc75f04fdf0873586a4d7afe88cb92c9cfeebf2aac2a4c15836ec6b27",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d8b3d19f20e2571c310c49349cbb35a2c53b9ed9c8b5d30402480fade61e834e.npz",
      "sha256": "23a9fb099ea2da38c43036ae06ba9e548324de863c5b9fa38c238b3f390ff059",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.18.post_feedforward_layernorm.weight": {
      "base_sha256": "3c327b7611f24a32db3b90b669bd356334cfdf090ee8764270740d7508343ab1",
      "changed": 2560,
      "content_sha256": "5aa78c7684f5133e7285ea090a9713147f1f713333447922e0961ea8e818c677",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "8ed52067aa07c8b327c623b80134363abfd6a81df9d14180f5bc7b91eec6fbae.npz",
      "sha256": "27ee06e1e56099b1c959edf9cfb3481968ee3e748e86d87306d7a398084f9a98",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.19.post_feedforward_layernorm.weight": {
      "base_sha256": "75e2c5e42d4281a971e80deda155f315db6255451a85e89d3f54ee596a941348",
      "changed": 2560,
      "content_sha256": "d8acccc32af1ffcb9fa17d4b8cdb5cb21ccadd01e91b9f72c46817d44865bacd",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "3068acd71bc65d5ccee8aa09feca75616b331b4c2253cc6f39ba58bf782c1c2e.npz",
      "sha256": "ea789a1c41a136459c9eb73ef331cd7666ded986982c8dff17785a903045a08a",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.2.post_feedforward_layernorm.weight": {
      "base_sha256": "7ba23c6e074a7d6013a6fe21970c0cc9361ed49862e1683934b065042963081d",
      "changed": 2554,
      "content_sha256": "4d473f9692486d9e32ae0850d77200797de21efa474afb231c59a9afea63d9d3",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d19217b9d6f7f301cc24a4416125918507b5732edcfe54fa1bb83d498316c4ad.npz",
      "sha256": "c5865e4cce3411af6e957196f3bd558955036e1391a67a9b4fe49d54cd2657b0",
      "shape": [
        2560
      ],
      "stored_coordinates": 2554
    },
    "language_model.model.layers.20.post_feedforward_layernorm.weight": {
      "base_sha256": "ea4337780feb9cf656408c00a4c19fd4e030dc9e8603c6133ae604bd4c6182c7",
      "changed": 2559,
      "content_sha256": "747419b02b0687686c391a2c012394af5b158b7f35e274fef0217c98efda49f3",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "be40af36f5e417b31fa9c0471fd7149391688a81381abf90817dfe4cc9294e71.npz",
      "sha256": "e2ca31065b4303540a860798c0ac6c58c997867a1c9fb2ea607255cedd9f644e",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.21.post_feedforward_layernorm.weight": {
      "base_sha256": "cbdc7a1f8b9a39fa3ae80c6e4d3afda42f54b3546f260838ffdc7043af8dee52",
      "changed": 2560,
      "content_sha256": "f8787f49ad8d7012e91f883cd1d4611eb8fe6bf5e17f0c2a093fa7bdbebd973b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "f8592e6c92b4d4951711f65302256615871212292c857b97d8416b52855d3c8a.npz",
      "sha256": "cefb6dcc16ea213854ed5db5bab2218e069bb23a009447bdaaef0e94c6e02368",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.22.post_feedforward_layernorm.weight": {
      "base_sha256": "7efbd4f118b8c50bb05627be77c5b4e7b65fb5b01e1771397497adb07087a29f",
      "changed": 2559,
      "content_sha256": "3275ff87c511df381c83d217d56b68de7f2590a862b5047c798930e9b4f40bef",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9b59f2432e6e5ff909e104077ee8b7bffba0d31a2c125d70280eb9f7aba4eab7.npz",
      "sha256": "d3a8cfec7c3922f6aba8b3f7cc46812710979d19eddc7c03fd8f7e51e5c97105",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.23.post_feedforward_layernorm.weight": {
      "base_sha256": "21cb1dcda168867e6ec841a27b8904b023b9e16b0ffef21d5aa5ae8083e17cf6",
      "changed": 2559,
      "content_sha256": "562d7670e2b77525b62e0dbdb3dae344f660b0f9f8f63ca512d30cd9fa91be8b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "57c66c318a5615f8a519c12b40043d971e39b8b236dcdbf035ba937cb04a6aca.npz",
      "sha256": "605ba301d95d6bc6a5e89e54a1ecab325be8b5ec6b5cf2ce970a300a4c009ac6",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.24.post_feedforward_layernorm.weight": {
      "base_sha256": "f90c30e774400f0a9eebd22d9220c281cde9db95366069119c4d09de860b0237",
      "changed": 2560,
      "content_sha256": "db4d9a5c6d541b899c5627067ee68b5a09de5e957a5aedcc3abd001e0bdcbc4b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0b1d6a382a000d64a01657b474a1e957b25748778db048ee42b59031e7693cd1.npz",
      "sha256": "8db72caf8b04c2d037981f1d663dee0be47035b9c1a15069e4cd1e668777b051",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.25.post_feedforward_layernorm.weight": {
      "base_sha256": "aaeebabe1fa818fe3388ded46efca3b2fcfe87049a70d1285411b23092793000",
      "changed": 2560,
      "content_sha256": "ff3f52bee99300b77be32d7b721fbf00edf47351be10e19ded9a4f9d3cb6b01d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "574a6b7ff84afdfdcfe2f010f66f879e6f9c8dc040987c39b43a0f3efada7203.npz",
      "sha256": "e8bfdcca46b03741afa716c64836420d38655a45e901637089f2892e312043a8",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.26.post_feedforward_layernorm.weight": {
      "base_sha256": "cd1d93d680e66e0c5649f4079d22f6afaca373da9d4f0df0c981b9e2273196aa",
      "changed": 2560,
      "content_sha256": "7e3efbf40291e8c8a2c0bcf1021e759cc0c199acb9ce1ddbcaaf41f8d9055593",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "af4c62bf12cd54912be9139e6e3992ff89db2aa89b3893fac489c2fbf1ceb48e.npz",
      "sha256": "910a243dc21d4be21e016b27fc0795442449ee149e557fda442756f2860285d3",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.27.post_feedforward_layernorm.weight": {
      "base_sha256": "0a0191055a177497217a5301b209bf912d04361bf09fcc934686406671142058",
      "changed": 2560,
      "content_sha256": "c54cea6aecd18d064d397bc1b4cc2cb9b5d484d4ada8526bcf67e2e8d011a362",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c01d30cf50acff3982f1344d5b19830e6021a1be84945b613a0e770a2783d9cd.npz",
      "sha256": "d41ed573d8fe661df5babb4263a97795ea52e88b37bd1c7e6d6269bb8dba2d40",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.28.post_feedforward_layernorm.weight": {
      "base_sha256": "5db6d15e40b990711ed9aa0552a195bd76eed7c5074cab2737ab13a8846e5038",
      "changed": 2560,
      "content_sha256": "63b32b69aec670df8a812d285fe6f39d061daad6bc67d08c755c4f5154f73d30",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9d7633e008ec94a56b6423be08fb87a8a04b57f4b061b97206d1a032ca1429a8.npz",
      "sha256": "71722284f723a1a9d97054096269b7d2dddd4c8609913035f6b8bfd7f73904b5",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.29.post_feedforward_layernorm.weight": {
      "base_sha256": "3c9b3122d708a2d60b44c233d10998d8e7b7c7ac6ea38cd836d7316ba2fd8972",
      "changed": 2560,
      "content_sha256": "818ca131fcfb3ba90fbf86a5155c771b02d169b6274e06ba083ec729ff771704",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "fa92473f5909de0227e5424a048e4bae0f313ba4a902991b75b39057753da0dd.npz",
      "sha256": "81e106456c54d335bb02e2f1d53cfdb6d2272a82fcae97a298f1053928249407",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.3.post_feedforward_layernorm.weight": {
      "base_sha256": "7cabe9ab9a7858d9c3e94a3e8f66b9f9b94007ab11007c63e2ff7263c5b74383",
      "changed": 2549,
      "content_sha256": "3854a6557436eb26a2caa01024df2b06f849898e3a90ec33b2b5735b427df5e2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "615261243226abac034054cbbf923da84686df97447bfdd44e26734596fa4258.npz",
      "sha256": "962bfec24adce6c8fd4a68a696fb806d2954e009cf2ed0e873918200c04b6ade",
      "shape": [
        2560
      ],
      "stored_coordinates": 2549
    },
    "language_model.model.layers.30.post_feedforward_layernorm.weight": {
      "base_sha256": "3b1038978f803988e5e6de2d5ddb2e696cbe84558b39f8645405a7bfa1ee50f3",
      "changed": 2560,
      "content_sha256": "184439e9fc5475f043005ca477bd33c8244b948aa0020b4653e3abc075816713",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c7195d7bbbf3ec90680d4cd156699f0ad9b611d9ddfc78b684046d1f6dc21c84.npz",
      "sha256": "0c69d170d72c086e1a070aefccecc37177df2de550f71b652e6e3c337288f4b8",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.31.post_feedforward_layernorm.weight": {
      "base_sha256": "25e5d11534379bcf874a73d739c8c47d4077ad2e66cac4ac99e0891bb1758f15",
      "changed": 2560,
      "content_sha256": "5ad79c2a314dd118b44731697f609ab14e7ae2b87b2fa5cb7059a58da24792be",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "822f1a8b17a51a9a82e221e664c005431e34783377660f9afbd7d10e0ef96992.npz",
      "sha256": "c6e01ff8928834a90bd18c9002c56f1b2249fcb0c1603b550074e1f6f7e471a2",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.32.post_feedforward_layernorm.weight": {
      "base_sha256": "1f490a1004857564bd05c5a631b0b5a6b40b7564042225a9a8ec65e1992e4476",
      "changed": 2560,
      "content_sha256": "f235e439f1ecad02294631c97d7b4e1e01f2d6f632beea86833361d92727a249",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "034e0acb9ca8b3bda13b3312468db3d84010807a503c4f61341b0d469032c067.npz",
      "sha256": "839afa3ba855029cab1a51bc224e73ee1ed30d6c732bb6903f27dc99f9132d5d",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 2560,
      "content_sha256": "4527503aee599f44b10156ecb32a4f92c51bc2cb802e2386658177f3a2f1524a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "4d10d981c6f1dc699592b2f9dc6203f6637d5786ea06a138dbecc70dcb8fcbce",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.4.post_feedforward_layernorm.weight": {
      "base_sha256": "0cbd169db1d4ae9e2c5cd546dae9fe997448c2af2f9ac682c0a368db8274a934",
      "changed": 2557,
      "content_sha256": "165ee08fa799827ad1d2f6a73adab88bb5e61b5bead984960678beccdecc0758",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "47402777e17d78ecc6523e21c921b515e730fc00545f0b66ba6465423c9c1de8.npz",
      "sha256": "b1a757bd6f802df766decc725ad7997ce3b924f04978df75526fe1aaa8eab863",
      "shape": [
        2560
      ],
      "stored_coordinates": 2557
    },
    "language_model.model.layers.5.post_feedforward_layernorm.weight": {
      "base_sha256": "50d2b10526e4e98e53be4e791087ccf1b8f00b14065981a8480d4707705eab85",
      "changed": 2556,
      "content_sha256": "51e416242dc58eeb5ae1105fa091b12224f9b68f1ac5ca0ab7fcbf6177aee90f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "721cf796c77ca19da54e1fadac9a960f3b191367320b198173d870a75e9fccf6.npz",
      "sha256": "cbd48c7699be273272d93a3dc054e8c294a61154344dea53be3986f8efa9ebd3",
      "shape": [
        2560
      ],
      "stored_coordinates": 2556
    },
    "language_model.model.layers.6.post_feedforward_layernorm.weight": {
      "base_sha256": "7a12e34412b076f6131e31747ab5396751f334b3fd00192be608f83e9db86051",
      "changed": 2558,
      "content_sha256": "506881917179204eeadbb17599eceb8e27a0fb03e507be80354f18b7d22a315e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "5dc5b2fd489c100c79bb238ad3b2e65e26153847eaf5c19b10bd8b413992d67e.npz",
      "sha256": "2559588be83dee3c44888cb0ce3bff0fb2286c764a74334f4fff192c5c051be9",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.7.post_feedforward_layernorm.weight": {
      "base_sha256": "4047ab8dd31dc5fe079ad664f9e9b9d1b224ede91a5bd71432cc6e1343d5ca86",
      "changed": 2558,
      "content_sha256": "b3becbaa4fe62f58eede3f4a8136eee9f36351e685190022ff5505e33d1e043e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b2542d99a990ca2076dceec5b257ba9f32acb35aa0b4e4f45ff206dcb6313e49.npz",
      "sha256": "422f32ab8f8247daf137fbaed33198ddda7aaf32e02e272c5f3fe1b31631c9d1",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.8.post_feedforward_layernorm.weight": {
      "base_sha256": "b0494c300d1bf8aeb1054b693e119bb4e046b3b1e39b302c9aa51648b4614f46",
      "changed": 2558,
      "content_sha256": "58b7defcfa0358c6c691f890e598e8b1b111dab531defab9521c1808e322c7ec",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4fdd0090a05f653dbc385da916a94c0f8e60b6fef947c4dcf6aaa8d6344ac18a.npz",
      "sha256": "560329805c771aaae5b87db3ea03b3bd03b5cf87fd3201f5cebda0c5be87aacb",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.9.post_feedforward_layernorm.weight": {
      "base_sha256": "26c6490dfd39ca7b613f8bf76ae4f3afc029c9ff89a1032f0b9f70d19df4980e",
      "changed": 2558,
      "content_sha256": "2e0830a5545313f3578c07c732a0710be9fef7f54b1f45c1e4428d534ef42aeb",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0c8e013044212b7472539090ce5481b7e2a763cfcb21d33d800f1e92faaf0830.npz",
      "sha256": "cd78a71b77dceef4e5e110b46899fe8e71fbd9711d5ebbc9c7a906b57ddede8f",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-ca8cbee98860677bf0a75be04d1f27223d5671d856123e1a97e8cbf0a498b80c",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4245689655172414,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 24,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 29,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 32,
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
    "format_errors": 3,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.1724137931034483,
    "repair_score": 0.1724137931034483,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第8轮

**当时目的与操作理由（原文）**

Candidate 8: restore feed-forward norms to W0 and set all 34 post_attention_layernorm weights to 0.95*(1+w0)-1. Candidate 7's increased feed-forward gain improved ordinary joint correctness but violated total-count cell protection. Test the complementary residual-balance change, without training or label-fitted parameter ranking.

**本轮原记录的主分数**：`0.1724137931034483`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 86107,
  "id": "c-592b297f763a65e45db565f6f64075dbbc7913ee757e5f38070e3f794e7a81e5",
  "l2": 863.1910891094433,
  "parent": "c-ca8cbee98860677bf0a75be04d1f27223d5671d856123e1a97e8cbf0a498b80c",
  "rationale": "Candidate 8: restore feed-forward norms to W0 and set all 34 post_attention_layernorm weights to 0.95*(1+w0)-1. Candidate 7's increased feed-forward gain improved ordinary joint correctness but violated total-count cell protection. Test the complementary residual-balance change, without training or label-fitted parameter ranking.",
  "tensors": {
    "language_model.model.layers.0.post_attention_layernorm.weight": {
      "base_sha256": "53d94cede36fe89aed217c6c2f629324743464ba8394052754a6dc75d6ac4bef",
      "changed": 2077,
      "content_sha256": "8388df6f71d13919b718537660ed3e02a34117e3ae0a29192baa5a0966f3b01a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "a77f005719dad6d425a413981170d6619aefc36947c70e804b0e1cb23ed747b2.npz",
      "sha256": "035e1b2dce7b0ac2e9d5e29d236c3044597a24e2655caf14d39c89e5a72263dc",
      "shape": [
        2560
      ],
      "stored_coordinates": 2077
    },
    "language_model.model.layers.1.post_attention_layernorm.weight": {
      "base_sha256": "3e22bcb473b0ecae1d93fde14cde1e84227e2b211e913150d835ce66a5047399",
      "changed": 2476,
      "content_sha256": "a131460889f7861ebd0a5d02c7b0f0281f2e75285843fbd052296ebec6705baf",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "bcdc10868b8ef17328a818d77525c29499eeee774dcb0741342e7b1339a91399.npz",
      "sha256": "e4f2e3e82dd2f580ed5886bd5b99690ac17150481c71fa9494590085de79b965",
      "shape": [
        2560
      ],
      "stored_coordinates": 2476
    },
    "language_model.model.layers.10.post_attention_layernorm.weight": {
      "base_sha256": "d054981e9a3909e58d35a04f4bda50ac2ead3dabebcf75d98658b537476d194f",
      "changed": 2546,
      "content_sha256": "901e4a3c45a7ed8b1f7bc58afe72deb2c314f6d21c24103b1afc50c570444d0e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "44e0f408e465ffe6495611eef5330ccd23ad7b1ff14090a0687f33ff9a1659b6.npz",
      "sha256": "264153a5b9bc8311d3dd97d47170e1bf9d0b2dbde37113b7deebb077e16f91d1",
      "shape": [
        2560
      ],
      "stored_coordinates": 2546
    },
    "language_model.model.layers.11.post_attention_layernorm.weight": {
      "base_sha256": "5696484f555d320e73d6ba86f877ada9781159df5a0944f8f0977b5100e60a3e",
      "changed": 2546,
      "content_sha256": "d7a4670a0dadf4473faddf730cab3cdbe02a4fca1593a8fbbbf02c8d5338f781",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d9a43481c8d9604d783a0fdba884a882f55050341a63b6333c21921d798ae174.npz",
      "sha256": "12fac2cb285cd9bf2d1cad0073dddaa6a4e70c4d964c76ac59d0de404a969479",
      "shape": [
        2560
      ],
      "stored_coordinates": 2546
    },
    "language_model.model.layers.12.post_attention_layernorm.weight": {
      "base_sha256": "be00db50fb24f487a26b6baba4701af7a1c1dd4096c9113875342abc0a0d8346",
      "changed": 2525,
      "content_sha256": "e8b17c4bdd3dd17ea159d5b494c32d04ca714a1c40520acbd58d09c20e4bcae1",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "153280aa8d04587f09541c8ed731b16aa07189e343d0f2154fc1078bdb82eb53.npz",
      "sha256": "2be317c58b7bbc4f1bff879de509668a6e2d1e281d03e1ced86e8b5522465cce",
      "shape": [
        2560
      ],
      "stored_coordinates": 2525
    },
    "language_model.model.layers.13.post_attention_layernorm.weight": {
      "base_sha256": "ca12c7dedab9a7d241fe5e657d586d50485daf6dcd8fb3aa466adb18a38f0514",
      "changed": 2559,
      "content_sha256": "aeb93f76f1daa65c5341a1f8ffba2c4b62a25e29605ad1ff5a6dbdd3beceff83",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b6d7f81cecd99215c788058f3f3995bb2d12558821784b7622c7138010134a0d.npz",
      "sha256": "16c1bd07e85d919a549d548a5cccdfb27fdbf6b9690019f43b11d25c64f8becc",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.14.post_attention_layernorm.weight": {
      "base_sha256": "4651834d1149ea7116fad91a61cab71a76f32c234a7d6a99375b5a062c8f915a",
      "changed": 2536,
      "content_sha256": "bf1e7b453321424992803a2d5c2cb05449da3ec3f51edff982a6d2168a9aef77",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7ea7969fd5f1ab4c4ace75e7ea646b93f78a4aa4ec3f195a5f02a69e19344277.npz",
      "sha256": "2a753c0080edfaef2b89feb39b687fb04f9e3dff41e20b9e6a747abba162243a",
      "shape": [
        2560
      ],
      "stored_coordinates": 2536
    },
    "language_model.model.layers.15.post_attention_layernorm.weight": {
      "base_sha256": "e89d0d63fd097bdedb1aa1dbf2a13ed85c1514c300737af3ce9702da4cdfd515",
      "changed": 2542,
      "content_sha256": "86feb59e89bf52f513d5a52cc0a4777698ccd4b109034d7ae252c11eb86211d8",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "cdd2afaa265a46b79b32fc239f8e11b39b7c61ea2419109f7fdf9dd5b3009207.npz",
      "sha256": "981d25617bed92003ca09713b1be4b8eb3347c4d6824cba8ceeb7748c7a39731",
      "shape": [
        2560
      ],
      "stored_coordinates": 2542
    },
    "language_model.model.layers.16.post_attention_layernorm.weight": {
      "base_sha256": "8f1ab8b0f2e0a29ef36fda64e3359ecf94d3e3be08b26b86c45a5213081f3cc7",
      "changed": 2552,
      "content_sha256": "e54408c47a0bcd6a9dffcad31cf0ba4c6154ffa9ab9db7c60e974fe39c783599",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "e8e4f005c19810ef333e55af5ed90b1e278c2d20574a86ea45e41b733bdadbc7.npz",
      "sha256": "93cd7f85953fb1c21ae89444c10d2b27b627268f6e5bfc5ba1af59e9ba60b1bb",
      "shape": [
        2560
      ],
      "stored_coordinates": 2552
    },
    "language_model.model.layers.17.post_attention_layernorm.weight": {
      "base_sha256": "803151ba6f589e26d756a6bd15fd8a036dc7ebbc35212e174f45aa756d9f3c1d",
      "changed": 2557,
      "content_sha256": "e45a04ec5095a407c8ea9c3e20a985ed292b2db7d7d67ce3b8d9314711886adc",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "916e8b8e25eaf1cbcee9430038dbb79cf6df7f4ea6770b9f985c20ef9804d3ce.npz",
      "sha256": "00b4bd7060864b02a82883cff8923bd30d95448f7ad62042c859b8ae62126629",
      "shape": [
        2560
      ],
      "stored_coordinates": 2557
    },
    "language_model.model.layers.18.post_attention_layernorm.weight": {
      "base_sha256": "916004f43c817e02e48f26b8f0667de27e862f4c129d1859281b6f2c7a64face",
      "changed": 2548,
      "content_sha256": "5f4fa1a98191af48e8fef7ca89bd32a7aa48e3d277106eb708b953c5b9e52990",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "25ed5483205611702afbc460b79169a115f17956ca0b8d69eec559b8dfa20822.npz",
      "sha256": "595950d060579ab45e3bc34f2cf36e7fc2f65e46f944eaa9aef2e03d14b27999",
      "shape": [
        2560
      ],
      "stored_coordinates": 2548
    },
    "language_model.model.layers.19.post_attention_layernorm.weight": {
      "base_sha256": "f1a80d33d927b8a8fceea41aa1944ff52af6520c5e81bd6a347c5f1d38660d8e",
      "changed": 2551,
      "content_sha256": "f2c1358dd08ecd8bac4729caa772b9b053856775c28d2e0b5243b77e2e2814ed",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "421a394db2609c35899edce702ab39dc86b39204f3150c4dd5bf86c9c7b9c034.npz",
      "sha256": "36cc9bb62c1993f817566e9847e85fc2e9a906632259387a21ef0a386ef8fb21",
      "shape": [
        2560
      ],
      "stored_coordinates": 2551
    },
    "language_model.model.layers.2.post_attention_layernorm.weight": {
      "base_sha256": "ed9281bdc2c5432cfae383b2d23f87c786952c275060323a3e65865930b4df12",
      "changed": 2504,
      "content_sha256": "ff31ae1c799c3416b9f73bd23e54d8147f4cb03e86cd03eb2eb1b29addfabc4d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "69c7bdf2f4c873274f24a08c21dabf23e5a9868d6e3d6d6294531f3f95ab05aa.npz",
      "sha256": "8d1b6c92cab1d4c01a76bcc73861e2d77ab6dff7afa2e9e6c461cbc3f695b265",
      "shape": [
        2560
      ],
      "stored_coordinates": 2504
    },
    "language_model.model.layers.20.post_attention_layernorm.weight": {
      "base_sha256": "37d43b8fe8806c7b65f16ed23fb31da5c03e92809439edec6a67cc36fef36cf8",
      "changed": 2553,
      "content_sha256": "607d48944220bfbb3e40ee9beb167e8a4b5d71d478678fb549907b474bdcf7a3",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "56d24b947f92935bf35acfba4eed7da061e82e0388529b0808899be2747c2e0f.npz",
      "sha256": "cb317f666ffac424c2f3ae199856d6bad78cacb39c820ddac24a2b49b2ae1cc0",
      "shape": [
        2560
      ],
      "stored_coordinates": 2553
    },
    "language_model.model.layers.21.post_attention_layernorm.weight": {
      "base_sha256": "ecf77d197405867dd66c81b67e21928dec89f220f6fb4d1e83307717650d73ed",
      "changed": 2558,
      "content_sha256": "0ad0ebd6548605cbbb2f5c4da6390f55f9c6d3fb7b9c0d4987295c0696d3a88b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "a7710d8cc61889ac1d754088355702d50ce867ecaa719b0a5d9629c40a22f5fc.npz",
      "sha256": "62dca6a09a17e3b85af3a2312ffcca02645080f40bcbf959eeed7356928cea15",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.22.post_attention_layernorm.weight": {
      "base_sha256": "e438e6b262b68709c8e715febf443e809d4d7b7e0f0321026e86fd1a8a736c08",
      "changed": 2555,
      "content_sha256": "f56656a56b44eef43a97a5888dc457951dc3068e8eaa621922545370bba70f0e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c4b6075ed6bf96b1a85c342e3bb4aaa1dbab78ff18940fc2f0a305456d5a8aab.npz",
      "sha256": "a48f3fb75cdbfc729943a108848e9f2d63d12bc1529ac0cc306e870723127ba0",
      "shape": [
        2560
      ],
      "stored_coordinates": 2555
    },
    "language_model.model.layers.23.post_attention_layernorm.weight": {
      "base_sha256": "cae8c662a24ed17bbc323f3ceb20df4342139bbc724ea2e07174bd04681ab965",
      "changed": 2559,
      "content_sha256": "c3f3d8d310514ac740cae8d82b2b32367c18a0158c660a2adce1f3a0b23c1cc4",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ae549643feded92676d56843c6fda4f7d18694e70e4e81059d68b857a742d331.npz",
      "sha256": "37a4c34abf7dcb017a456ee11a6080517651857770556b04600f2215f6831415",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.24.post_attention_layernorm.weight": {
      "base_sha256": "5e264fcb54311d8adc92a04fcd41900703dcfe7596288e738e8e8cf94fefc7fe",
      "changed": 2559,
      "content_sha256": "e93ed4d3e36702fbec76ef801c81028d2f7b2006fb05dc500b56b1a0e4ee9de8",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "3e2a774e069b274c4e65f77f4649bce59b9516c4825acd479efb3e59a3b6addb.npz",
      "sha256": "584e36b871d40c270b3d63d8ed3bf78dd1acbbeabcb1c574a4dca4b4438b4122",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.25.post_attention_layernorm.weight": {
      "base_sha256": "6318814e677e136b4763ca87fb583311e6f59321ba82d24c57f65e57688d6785",
      "changed": 2560,
      "content_sha256": "33dc6dcecd46e6cf39bc757b7f9e99286104fdca84ef01c570079b760ba71bd7",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "1bdfa08873daf3a0b4ac8ea8f267241fff359623fb05d0c2a5156ec1a320c36f.npz",
      "sha256": "7f61bbce552838188336f3518bbedb826bc684e91510c15b952c614682ec017d",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.26.post_attention_layernorm.weight": {
      "base_sha256": "932efdf65ef698d03de6debddf59f24874a1595c77c3edf87a029dd3175c4ad5",
      "changed": 2559,
      "content_sha256": "0f229549d5b07b6570855b16e09154bcea003359410c8dc4ff2af53ad12cfbfa",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "77086caef1f7fdf9e67880748ec0ed0e6719785fa853224bce10a99074222b54.npz",
      "sha256": "16dcb45a01f66282b83ebe39a1052a7784494c56355416983adf062890244082",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.27.post_attention_layernorm.weight": {
      "base_sha256": "5b7b766c4fecaa3af0599d09cd942ec9150a8b700d34649b884b0967f25e2387",
      "changed": 2560,
      "content_sha256": "dfaefeb91728b2218bfc4b3501ea0af6a13d0ac23fc6793fcd54d360f0bfbe10",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c57181aed55878f2b32de1ae68b53ab5f4553f808658bb7fb7f1239d062980f4.npz",
      "sha256": "e27c311c78c0201ba2946e6d0309f73a82787e192d0e0d3e057e52a290c78fde",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.28.post_attention_layernorm.weight": {
      "base_sha256": "d8dfc712698540d6951844fc2d3715f1a97fb7fced831649f384a238a16e3832",
      "changed": 2560,
      "content_sha256": "904fd56bf8a631f236ef4539ba107387c9408fc24c9f374f1371a7cb843f4b84",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7e4c6f13a000c9db06f01e7e846ef56b712cda7e9038c0d1205ee2ad1260a19e.npz",
      "sha256": "ec90c70815b4596aa450c8a9b772f22a4d85388ea73b43f25a8d41643e3c8207",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.29.post_attention_layernorm.weight": {
      "base_sha256": "c2f6544e0d961568c20d6acf6a08d69ef732e67a08414264cf7a22d533168943",
      "changed": 2558,
      "content_sha256": "cff246e33a59db2ced41e75b058624ba3241ba21a43f56e07f02381467ce93d6",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "da7cd558ac798101726155e7974aad934f5a5d360a285b6fcd7c47dd955a40b5.npz",
      "sha256": "3b9a605f2c8f4c7ea1dd5c370dc06176562b710937ceb9c96e1a4557be2b0933",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.3.post_attention_layernorm.weight": {
      "base_sha256": "37b3d36eb7d61af802a12a4c064186b15ca10ab12469b33c9775f3a6d813b1f1",
      "changed": 2552,
      "content_sha256": "2d6e47de60465824746518b0dc6b4d69c8db4237081de3fb0bd5fe8e298dada5",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "deeaacc8314911f7d80d39e122347e77e30633d0941d5df20b1aaf4ed3dc615b.npz",
      "sha256": "6651c9b74eb903a48d6f7f715b75e95b944be8769644aff9f7bf29c53b634ef0",
      "shape": [
        2560
      ],
      "stored_coordinates": 2552
    },
    "language_model.model.layers.30.post_attention_layernorm.weight": {
      "base_sha256": "e0943a6f0643e2664491a1ec50f1f2850738bfcc99f45c0775645b14c6b3ea11",
      "changed": 2560,
      "content_sha256": "b309132b4070c302751658e95354cfb1610bbd792aae6f6814aa78e4f302b27e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "011c62170f811e20610cffa220f4205d4ed1da27ce2a11c03d629391a38e64c0.npz",
      "sha256": "7a2067a615f80440e634ef0f1655ab04e569989e3bb4c4abc4a3679092734785",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.31.post_attention_layernorm.weight": {
      "base_sha256": "925b5564431e6b26598995d6edc0cf2b2cf9d8b9b883cb22201dd7c572e59850",
      "changed": 2559,
      "content_sha256": "0ec5bf48f99896f022182096ce6ce9f8d35750d556aa3f60defbbe1196963641",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7bad0c49d4a37332d9e69fcec6c7b2f1945b1eabb11e482de0dcb6ed5eca965c.npz",
      "sha256": "5abd9080e61167532674ac758ab709f94c8f093220ff51a0c1f9cf37d9902951",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.32.post_attention_layernorm.weight": {
      "base_sha256": "a04b1dc858c775c5042fb8ad6c5a0438ef784fc8dac40e72e15f5900a0758688",
      "changed": 2560,
      "content_sha256": "a8000ebcc54a823cbdc625aadeb83c4b4bafa19661ac47027406efdb8f510044",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "98c92d72de663bbf335913c29c73230a435fd3d5da3292588f02a9f387166da0.npz",
      "sha256": "17b1895310d2b99b7f31e7da8d69dab05d0c4dc86c4bb198a50251d4d6a09c74",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.33.post_attention_layernorm.weight": {
      "base_sha256": "3fb756cb8c482f940baeb49ec47ae21d2b612ae83fe4f1bbdf8ca566b35d126e",
      "changed": 2559,
      "content_sha256": "61ef12e3aa004723a7200c5f6b5653845480afe281d034af7c54a776b0999f54",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "29323b0704970fa1e660f1405f812417f1c293aa7a7433c972338661a92e213a.npz",
      "sha256": "efd1181e36a0d54d54e2db887ee1f4844baccba51aaeecfba751df82b8131e1f",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.4.post_attention_layernorm.weight": {
      "base_sha256": "a205e703219f2894aa0debbde39583c857d97b2b71a9c9a266fc367de64f489d",
      "changed": 2534,
      "content_sha256": "75f8caa1f1bb7213f120dbe2b0491ab77a742bd6e65e54f0d2a8950016ee0a7d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b2d750b44cb392f5a09dd6fa4771350af7c2d00fe7dd8511204d12373edc4bce.npz",
      "sha256": "1045c73e4a4f1f48c6bd43f5a70bddf2d68442ffe4b9cc22e4ff8d74e2be0729",
      "shape": [
        2560
      ],
      "stored_coordinates": 2534
    },
    "language_model.model.layers.5.post_attention_layernorm.weight": {
      "base_sha256": "ad676442ed1551aea51af6bff08ce55594cd57d5fa2dbee76c884a98b0b7253a",
      "changed": 2549,
      "content_sha256": "5ab50ec9b6f244e15aa47b3ceb7a781065ba8d21d2602fe4f0b896678b91efca",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "45828bb9a9383ccdaff413a4eb26f7250a9ad43efc7720b351f01ef5fc4034f7.npz",
      "sha256": "3139fa4f86278fbdb1c2e268c87aac01a1983191a9d2919c9f4c527977ac3a04",
      "shape": [
        2560
      ],
      "stored_coordinates": 2549
    },
    "language_model.model.layers.6.post_attention_layernorm.weight": {
      "base_sha256": "d116d4dc1c63b2a4e5dc763b5f26907f5bc7e8ae646373d18752e06b1d503e75",
      "changed": 2513,
      "content_sha256": "985e921afa171c44d98a475d6daeaedbc35bce6269cfef18009699e55ac3b1df",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "2143c4a4c71ef53ff396ce91d74fbbd89a7d3b2f8190dd7887a62bae4978cc63.npz",
      "sha256": "c955def096fd177224591e195ae990f8ab653da2be760cf538f2ec2318d4ec8c",
      "shape": [
        2560
      ],
      "stored_coordinates": 2513
    },
    "language_model.model.layers.7.post_attention_layernorm.weight": {
      "base_sha256": "dd638d0d950e249ce01273d2ab3ddffbcd1a9daad984f6f0b37c54214a4e7c1d",
      "changed": 2542,
      "content_sha256": "2caa86b38f32d1eff05cc1b72d561ac8bd337d8130269bf9d1120bf7d8956980",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9bcbd8279fbafac857fc232d33351f52941ecd4bbd0c4dbdd1d42248c949cbea.npz",
      "sha256": "8ed40199cdecc0be491a1b35938dc7334a489d8e584e6e52d262251e6d7eb4d7",
      "shape": [
        2560
      ],
      "stored_coordinates": 2542
    },
    "language_model.model.layers.8.post_attention_layernorm.weight": {
      "base_sha256": "0eaadc2fd18af6eeff6993953e8d846875a69833412c41e7b80fe85f15731afa",
      "changed": 2545,
      "content_sha256": "5ed736422b5a669714cb3b47d920fcfac05184a6371b858966bbaa949763a84b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4d140546f150614bb02c51a67da2db32558363aadac4ce29abb47956c86d1615.npz",
      "sha256": "f33839b905701e52c5720d01d038da388fbaf39b0762249206297a267aa3a7fe",
      "shape": [
        2560
      ],
      "stored_coordinates": 2545
    },
    "language_model.model.layers.9.post_attention_layernorm.weight": {
      "base_sha256": "714bbce43eb9e0214ff97b76afaff8d14e78bca01268945de4285d0610d8fd1a",
      "changed": 2534,
      "content_sha256": "9cd06aedbc97671977bde877c18194558a101e4ebad18cd1cc3295f81a8e3b0a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "67183f359385738eb1515a527f09dd7b8a3704eafe00c0fc9adacb077df10b21.npz",
      "sha256": "a4cfb11a3494ee315cc367609f4f2cc3109991af17e5cedf79185db31d52644c",
      "shape": [
        2560
      ],
      "stored_coordinates": 2534
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-592b297f763a65e45db565f6f64075dbbc7913ee757e5f38070e3f794e7a81e5",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.41594827586206895,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 25,
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
        "correct": 19,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 32,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 35,
        "n": 58
      }
    },
    "format_errors": 3,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.1724137931034483,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第9轮

**当时目的与操作理由（原文）**

Candidate 9: independently W0-based, restore attention norms and scale all decoder post_feedforward_layernorm effective gains by 1.02. Reduce the magnitude of candidate 7's direction because both reverse-balance 5% edits improved joint correctness but violated total-count protections. Development-guided scalar choice; no training or label-fitted channel ranking.

**本轮原记录的主分数**：`0.1724137931034483`；保留原始0–1尺度。

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
  "changed_scalars": 86956,
  "id": "c-d0c442a99494bee4870b97531b5fa439a2bd85addcd63e098acee10837c21119",
  "l2": 545.0019619340414,
  "parent": "c-592b297f763a65e45db565f6f64075dbbc7913ee757e5f38070e3f794e7a81e5",
  "rationale": "Candidate 9: independently W0-based, restore attention norms and scale all decoder post_feedforward_layernorm effective gains by 1.02. Reduce the magnitude of candidate 7's direction because both reverse-balance 5% edits improved joint correctness but violated total-count protections. Development-guided scalar choice; no training or label-fitted channel ranking.",
  "tensors": {
    "language_model.model.layers.0.post_feedforward_layernorm.weight": {
      "base_sha256": "4d1ae452b9efcb6e878416337ad5ea9bb74f5128109ba117b1efde7f38c0589e",
      "changed": 2540,
      "content_sha256": "b63be69ad4aa1f097ccadb0164402a9fbcbde2bf58a17c9c9a3083d6d5e82c56",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "5ba727d69136394583fd603b63395a05540ff515454522e9fad8fff136e9ab77.npz",
      "sha256": "71520c9d1ed370f127fee4be64881967c54332ae2a35b582a2f253b03b999158",
      "shape": [
        2560
      ],
      "stored_coordinates": 2540
    },
    "language_model.model.layers.1.post_feedforward_layernorm.weight": {
      "base_sha256": "34d9e47dcac71d0fad930e7d9e0955af667b643dc3a866c5970ce36d10a4e214",
      "changed": 2555,
      "content_sha256": "d05000d7fe38aea63d4696b7b30b13769d3933b96e487fd9f12649b57f4c8f8f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "3043785de03184f7d69b59c2bbae1def7875c5f86e5ec79bc04560a7e52fac8c.npz",
      "sha256": "2421e9cc259037819d63572f004891c1542509accd8f0abf69b8013fa0ba4196",
      "shape": [
        2560
      ],
      "stored_coordinates": 2555
    },
    "language_model.model.layers.10.post_feedforward_layernorm.weight": {
      "base_sha256": "af7761db8fb6d65d7a92deced7aa6ed9ab39d59ee3f31efbf19eff7359129043",
      "changed": 2558,
      "content_sha256": "1b987a664033992ffc958b71e4314e853e1216502c3fae9ab443a20d94343592",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "72f7688908dd4021f31f16b0ab7bcd5e283e44fbb3079a8c543be98fec663b29.npz",
      "sha256": "eba6f38250f0a7c526f09d890adc48366cb43c57ecda8bf27728af8de51ed0d3",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.11.post_feedforward_layernorm.weight": {
      "base_sha256": "89d384f0b663a59798d0caf3817acf749d1286ee7fa658a800e45949f2bf9d2c",
      "changed": 2560,
      "content_sha256": "5080b98d71e7d7ae2f3ef2f1e2eb1ac6b0497b2c9fa28d34674b94754c51f887",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "33d2fe715bbaf79c665524c2c134192d6c81f83225430f58ac440f64aea9d0a6.npz",
      "sha256": "c24f25727612b8d93e41bc0bf28bd8b86f89bc14cee682ed73829f637f84dc70",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.12.post_feedforward_layernorm.weight": {
      "base_sha256": "f04a87a55283cc720a8ed1ea93c3ea3e3998176474beb56db26e85dcdd82fbee",
      "changed": 2559,
      "content_sha256": "f8f505d628282d70f7246067e928893d8d626414d70891f7793d0eefeb0dc020",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "364856f727b13766a6dfe092412499e3804b1779e79a98d5d17f571f785f01b0.npz",
      "sha256": "772bab6f582a809d3a1ad7c939a0d9efbeac22d9b753f69aca0b1df4cb24774e",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.13.post_feedforward_layernorm.weight": {
      "base_sha256": "f595e44e15f2081870bdfabfe3cd8aef4c5e22bc5f0000b595d59e401df29de3",
      "changed": 2560,
      "content_sha256": "92964d96ef332debfaca35c59bc12be800066754221e98f9cf777232ab710f62",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "55908453b2eaf90446af4573a8423cf9ca877947369821efec861e6d5152b13f.npz",
      "sha256": "20454f192562233839f0706acca2d3488ac728f8695c039207b0808c6c19b7de",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.14.post_feedforward_layernorm.weight": {
      "base_sha256": "f4ab4a625f4d59c621557cf3f253fbf7c265bf356d1dd97604a6544d49895af5",
      "changed": 2556,
      "content_sha256": "c6bc1b8aa9a63f6707eacc74c3883063c81c9ff5d22551202ec014058f65f5f0",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0ff4502ecd17ade201c3be3ba5bd899c24748fe17975d199c57a4d29ad1beae8.npz",
      "sha256": "b52bfa4bfe3ae3796db6b6108837461cee80e896b548aecb5b160b7a1bd9f003",
      "shape": [
        2560
      ],
      "stored_coordinates": 2556
    },
    "language_model.model.layers.15.post_feedforward_layernorm.weight": {
      "base_sha256": "c3a0ecc631fc86eeaa78e7d6351f2659cebf1132b856183277b448f8db983d4f",
      "changed": 2559,
      "content_sha256": "c8914e96ae96a01f978f5d37eb6c9f4557e5c6f48388934ebd94c1ab55b53572",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "bee0d6867067a9e42d89014f4d3d7bb008f720190fdd6f0d9ba6bc41cdd817c5.npz",
      "sha256": "232a9b894fa0474808c6e9e4b55d01e41e1fb96c8f68ca72ce1dfe5b594a793b",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.16.post_feedforward_layernorm.weight": {
      "base_sha256": "83b002dc6701177b1aa90dac5d981fe3cf205a63210de97a2759e071b22afa99",
      "changed": 2559,
      "content_sha256": "82a743fee2f06b63cd7d34794960efb37f3848ee85a80729cc7ffc12b8604a82",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ccc477cd6b70843cc0218c101088bfdab11a1f3af23336a1df20fae85f1c8c6e.npz",
      "sha256": "a479323f55c0764d18a3dbddcf76f0e8c9b6ed707d4c168a2505375be2f5391f",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.17.post_feedforward_layernorm.weight": {
      "base_sha256": "909c707fd7898fe36b26ffdc0e92d398396ffb50c4872e5f9744236bf6ff5cf5",
      "changed": 2559,
      "content_sha256": "b414b057c4ad52a8d8e8468e613b20e60abd7f7861014fb9dc3317c5bef41c83",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d8b3d19f20e2571c310c49349cbb35a2c53b9ed9c8b5d30402480fade61e834e.npz",
      "sha256": "02ab829eb546170e03ff4ba5697bfb6dc33860d7559c0b6da75ed94c7b5c99af",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.18.post_feedforward_layernorm.weight": {
      "base_sha256": "3c327b7611f24a32db3b90b669bd356334cfdf090ee8764270740d7508343ab1",
      "changed": 2558,
      "content_sha256": "35954d353c710727d05264620eb79eb46107609b18bf821adf97f002232332af",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "8ed52067aa07c8b327c623b80134363abfd6a81df9d14180f5bc7b91eec6fbae.npz",
      "sha256": "a77c036c1e07b103a2eb14c4bdc4f53f856f4cbb24e0a0452bda24ec807bd8cb",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.19.post_feedforward_layernorm.weight": {
      "base_sha256": "75e2c5e42d4281a971e80deda155f315db6255451a85e89d3f54ee596a941348",
      "changed": 2560,
      "content_sha256": "9b9f8bbfab965b4244a78ac20b74e5e8f428ab54635fbfe060c6247198908967",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "3068acd71bc65d5ccee8aa09feca75616b331b4c2253cc6f39ba58bf782c1c2e.npz",
      "sha256": "4d1f3ffbf6de532ded1029f519e0d49f0abd6262c8f48f71b3d06bee2dcaac26",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.2.post_feedforward_layernorm.weight": {
      "base_sha256": "7ba23c6e074a7d6013a6fe21970c0cc9361ed49862e1683934b065042963081d",
      "changed": 2554,
      "content_sha256": "1e818ccc8a579f820d6207f4f0244753aae7a50398a812d9db981cc12aa26587",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d19217b9d6f7f301cc24a4416125918507b5732edcfe54fa1bb83d498316c4ad.npz",
      "sha256": "70d909f9bca3b706eca55c2c3ee917de878dab977f55d86d60cffff86a2c1f14",
      "shape": [
        2560
      ],
      "stored_coordinates": 2554
    },
    "language_model.model.layers.20.post_feedforward_layernorm.weight": {
      "base_sha256": "ea4337780feb9cf656408c00a4c19fd4e030dc9e8603c6133ae604bd4c6182c7",
      "changed": 2559,
      "content_sha256": "cae83856df1406da32cafbf5e5308fa7ce3d06fccbf4b59fcd004fc9a34cafa4",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "be40af36f5e417b31fa9c0471fd7149391688a81381abf90817dfe4cc9294e71.npz",
      "sha256": "7c68de7897079b91bc91a83fc8f1edee8b02fc7126d158216880ef1b8ebd487e",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.21.post_feedforward_layernorm.weight": {
      "base_sha256": "cbdc7a1f8b9a39fa3ae80c6e4d3afda42f54b3546f260838ffdc7043af8dee52",
      "changed": 2560,
      "content_sha256": "36ba9710fb42465c740eaecec745f7c988946b09a9582dd32777ce86a113de9d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "f8592e6c92b4d4951711f65302256615871212292c857b97d8416b52855d3c8a.npz",
      "sha256": "5c2b03e3a68698949a0e4776157a3030770c6190739f80b9c886fe72684d1cb4",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.22.post_feedforward_layernorm.weight": {
      "base_sha256": "7efbd4f118b8c50bb05627be77c5b4e7b65fb5b01e1771397497adb07087a29f",
      "changed": 2559,
      "content_sha256": "7ae66912a9b164986126a13661035804775e377ae28d089d19dc6ee6e82bcd06",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9b59f2432e6e5ff909e104077ee8b7bffba0d31a2c125d70280eb9f7aba4eab7.npz",
      "sha256": "5df7de45eef365760b155fb178606a6312742c3f4ca83b32cddf34ce13492616",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.23.post_feedforward_layernorm.weight": {
      "base_sha256": "21cb1dcda168867e6ec841a27b8904b023b9e16b0ffef21d5aa5ae8083e17cf6",
      "changed": 2559,
      "content_sha256": "9329fc9e4056cc819970e9b8ae716e4a59df6be9e036f483ba663ae1eff51b4a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "57c66c318a5615f8a519c12b40043d971e39b8b236dcdbf035ba937cb04a6aca.npz",
      "sha256": "fd3846f0382a4347d7e3976fc332405c467096201ade6c43401e4a71ad07d18a",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.24.post_feedforward_layernorm.weight": {
      "base_sha256": "f90c30e774400f0a9eebd22d9220c281cde9db95366069119c4d09de860b0237",
      "changed": 2560,
      "content_sha256": "24f1647772a364fa8c4d7afd9d3ce6c3e24e4c4ba6f20465da013497e61e3321",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0b1d6a382a000d64a01657b474a1e957b25748778db048ee42b59031e7693cd1.npz",
      "sha256": "9582e1fbcdbe78d9ccc15f120bd691a9ad6910ec9b4d8845bd1f98722ec0544d",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.25.post_feedforward_layernorm.weight": {
      "base_sha256": "aaeebabe1fa818fe3388ded46efca3b2fcfe87049a70d1285411b23092793000",
      "changed": 2560,
      "content_sha256": "330f79bddc5114815b7f70b87ed784676f8b5e167a8c24b98598d05c9f7ab74e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "574a6b7ff84afdfdcfe2f010f66f879e6f9c8dc040987c39b43a0f3efada7203.npz",
      "sha256": "230588f7fcf8fb9b2a75afcd389daf0bbcd6e217d278e92c79f2a19e36f26e1c",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.26.post_feedforward_layernorm.weight": {
      "base_sha256": "cd1d93d680e66e0c5649f4079d22f6afaca373da9d4f0df0c981b9e2273196aa",
      "changed": 2560,
      "content_sha256": "e8adb35c2b9396c40df1c5a51c417e1980634a100705d7efe60905943a08e6d9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "af4c62bf12cd54912be9139e6e3992ff89db2aa89b3893fac489c2fbf1ceb48e.npz",
      "sha256": "087e335d0abaa1a8cc7568389c767d527f387c97f3d7bc709fe51750df9ba050",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.27.post_feedforward_layernorm.weight": {
      "base_sha256": "0a0191055a177497217a5301b209bf912d04361bf09fcc934686406671142058",
      "changed": 2560,
      "content_sha256": "4a9357e3a35c0b16ce38b0e1a44cff4712b224ad0b872f8b52857bc575d25961",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c01d30cf50acff3982f1344d5b19830e6021a1be84945b613a0e770a2783d9cd.npz",
      "sha256": "df67f8fd59a5ce5a7e1f7c6cdc539806f89709cae2197fd07692958a5be9a181",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.28.post_feedforward_layernorm.weight": {
      "base_sha256": "5db6d15e40b990711ed9aa0552a195bd76eed7c5074cab2737ab13a8846e5038",
      "changed": 2559,
      "content_sha256": "0850c209ff07186a0c68c2eeb914f4d56bb1b05eae62bdaf564c0ea8742279be",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9d7633e008ec94a56b6423be08fb87a8a04b57f4b061b97206d1a032ca1429a8.npz",
      "sha256": "40696c0ad5f035fe701bd5fa487f71a04cc27f77256313f3368ede55e5f488a4",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.29.post_feedforward_layernorm.weight": {
      "base_sha256": "3c9b3122d708a2d60b44c233d10998d8e7b7c7ac6ea38cd836d7316ba2fd8972",
      "changed": 2560,
      "content_sha256": "bcfa4e7debe61ac3cc587d514a77c6aec2cb37efb2f542676a9a7629625d62e9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "fa92473f5909de0227e5424a048e4bae0f313ba4a902991b75b39057753da0dd.npz",
      "sha256": "508454e4b1843822e33efbdb08e7796a75f3f5ada530c41874025e92648ed39f",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.3.post_feedforward_layernorm.weight": {
      "base_sha256": "7cabe9ab9a7858d9c3e94a3e8f66b9f9b94007ab11007c63e2ff7263c5b74383",
      "changed": 2547,
      "content_sha256": "da7ad52e3ae1fa6063a8c17845cb746e9d3cd312a098ceb2b79e835fab1aec0f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "615261243226abac034054cbbf923da84686df97447bfdd44e26734596fa4258.npz",
      "sha256": "d8b511de986ee88892742daf2460e1314b7463159bd5df986979a378a37d2365",
      "shape": [
        2560
      ],
      "stored_coordinates": 2547
    },
    "language_model.model.layers.30.post_feedforward_layernorm.weight": {
      "base_sha256": "3b1038978f803988e5e6de2d5ddb2e696cbe84558b39f8645405a7bfa1ee50f3",
      "changed": 2560,
      "content_sha256": "04656a12e11737c98abdccd10e7bd58b44dce8aed91b1550f15c6df9efec4283",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c7195d7bbbf3ec90680d4cd156699f0ad9b611d9ddfc78b684046d1f6dc21c84.npz",
      "sha256": "862003e77185792aa43ca6b7e29c56509c1dfe3699c36dd66ce684c3518de0e5",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.31.post_feedforward_layernorm.weight": {
      "base_sha256": "25e5d11534379bcf874a73d739c8c47d4077ad2e66cac4ac99e0891bb1758f15",
      "changed": 2560,
      "content_sha256": "6a142ef0bff0bcf3bd83521e2ad82962995cfe38cbc67b7d96c8e812902f59a0",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "822f1a8b17a51a9a82e221e664c005431e34783377660f9afbd7d10e0ef96992.npz",
      "sha256": "a5f2f1c0382feea54d060352d052e43a3ebd4de90cca8ce8c3ed7ce041333b02",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.32.post_feedforward_layernorm.weight": {
      "base_sha256": "1f490a1004857564bd05c5a631b0b5a6b40b7564042225a9a8ec65e1992e4476",
      "changed": 2560,
      "content_sha256": "855a914174646902ea2f27afcc464af315865516ce09a6bb172772b4d71cbbe7",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "034e0acb9ca8b3bda13b3312468db3d84010807a503c4f61341b0d469032c067.npz",
      "sha256": "4c9cfccd5a0fbfecbfc837dae84b18f7da86af7319849d3c1a72163f70e50a22",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 2560,
      "content_sha256": "4ab4652f815a4668445e10af9370ba2531411f57ad9debf1ad19a26440f3200f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "9b6de7c4bec5f97cca3a936e836d43f8a2ec1bde2c83068cf6613e9c9cb4d441",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.4.post_feedforward_layernorm.weight": {
      "base_sha256": "0cbd169db1d4ae9e2c5cd546dae9fe997448c2af2f9ac682c0a368db8274a934",
      "changed": 2551,
      "content_sha256": "0772cbe8b4ed7d91ba23d7ae50c8585a98c05cd92da197e8b3b933e314e0a92e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "47402777e17d78ecc6523e21c921b515e730fc00545f0b66ba6465423c9c1de8.npz",
      "sha256": "692911cb3b3646c72141df53a9e331920c8d1952bb986022fae558ab31b22431",
      "shape": [
        2560
      ],
      "stored_coordinates": 2551
    },
    "language_model.model.layers.5.post_feedforward_layernorm.weight": {
      "base_sha256": "50d2b10526e4e98e53be4e791087ccf1b8f00b14065981a8480d4707705eab85",
      "changed": 2556,
      "content_sha256": "5a33621a8cf57494e7d6e1d7e430d5483f6b00a7910aa9a059e2f4bcd5248ebd",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "721cf796c77ca19da54e1fadac9a960f3b191367320b198173d870a75e9fccf6.npz",
      "sha256": "3d44fbdf5abbb863b7761732648642c9b946c8188ec1c29cad6800bd36bef8f5",
      "shape": [
        2560
      ],
      "stored_coordinates": 2556
    },
    "language_model.model.layers.6.post_feedforward_layernorm.weight": {
      "base_sha256": "7a12e34412b076f6131e31747ab5396751f334b3fd00192be608f83e9db86051",
      "changed": 2557,
      "content_sha256": "65294ef1649e01a5bf10700824567a6586c784f0f99b6d00031478024125f3b9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "5dc5b2fd489c100c79bb238ad3b2e65e26153847eaf5c19b10bd8b413992d67e.npz",
      "sha256": "782d860db522133718ddb0508c6e24e8f7b3ed8abca37aa32ee8ec4bd1dcf815",
      "shape": [
        2560
      ],
      "stored_coordinates": 2557
    },
    "language_model.model.layers.7.post_feedforward_layernorm.weight": {
      "base_sha256": "4047ab8dd31dc5fe079ad664f9e9b9d1b224ede91a5bd71432cc6e1343d5ca86",
      "changed": 2557,
      "content_sha256": "164e973066208d4a6a72866fb25d6dc0662233aca8e7c3bb02f53fe752132804",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b2542d99a990ca2076dceec5b257ba9f32acb35aa0b4e4f45ff206dcb6313e49.npz",
      "sha256": "a8e8c2122cf69e493de8479a05fdf0844fb58c0bb2912462fce44472f7ba70ac",
      "shape": [
        2560
      ],
      "stored_coordinates": 2557
    },
    "language_model.model.layers.8.post_feedforward_layernorm.weight": {
      "base_sha256": "b0494c300d1bf8aeb1054b693e119bb4e046b3b1e39b302c9aa51648b4614f46",
      "changed": 2557,
      "content_sha256": "7f69b4b112ae68e934fec093165d306eeb7e9ffc5e03f77cbbcc95d140e55ce9",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4fdd0090a05f653dbc385da916a94c0f8e60b6fef947c4dcf6aaa8d6344ac18a.npz",
      "sha256": "b7dddf992aed885ee481045a6bda7e0f32966ad9b74582e8d8095fc43ba675a3",
      "shape": [
        2560
      ],
      "stored_coordinates": 2557
    },
    "language_model.model.layers.9.post_feedforward_layernorm.weight": {
      "base_sha256": "26c6490dfd39ca7b613f8bf76ae4f3afc029c9ff89a1032f0b9f70d19df4980e",
      "changed": 2558,
      "content_sha256": "a7c398de4e0a662bf7c33eb2d3103ce7af3020789fbe4647a7f990bbe06fffb4",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0c8e013044212b7472539090ce5481b7e2a763cfcb21d33d800f1e92faaf0830.npz",
      "sha256": "fe9909354e6dfc10d48ad134b8d21c906c86b95a52456b7cc6b6721522079ae0",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-d0c442a99494bee4870b97531b5fa439a2bd85addcd63e098acee10837c21119",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4245689655172414,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 27,
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
        "correct": 18,
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
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.1724137931034483,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第10轮

**当时目的与操作理由（原文）**

Candidate 10: restore all prior edits to W0, then apply effective post-feed-forward gain 1.05 only in decoder layers 23–33. Global gains 1.02 and 1.05 improved ordinary joint correctness but failed total-count protection. This coarse depth-localization test seeks separation of benefits and regressions; layer interval chosen for exploration, not an established defect or fitted neuron ranking.

**本轮原记录的主分数**：`0.1724137931034483`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-2004fb1f5ec2486fdc14df5fb5cf04396b6fb0fbe4a12b31d037a9a9f7bfb6d0",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.1724137931034483
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 28159,
  "id": "c-2004fb1f5ec2486fdc14df5fb5cf04396b6fb0fbe4a12b31d037a9a9f7bfb6d0",
  "l2": 1283.6413443209537,
  "parent": "c-d0c442a99494bee4870b97531b5fa439a2bd85addcd63e098acee10837c21119",
  "rationale": "Candidate 10: restore all prior edits to W0, then apply effective post-feed-forward gain 1.05 only in decoder layers 23–33. Global gains 1.02 and 1.05 improved ordinary joint correctness but failed total-count protection. This coarse depth-localization test seeks separation of benefits and regressions; layer interval chosen for exploration, not an established defect or fitted neuron ranking.",
  "tensors": {
    "language_model.model.layers.23.post_feedforward_layernorm.weight": {
      "base_sha256": "21cb1dcda168867e6ec841a27b8904b023b9e16b0ffef21d5aa5ae8083e17cf6",
      "changed": 2559,
      "content_sha256": "562d7670e2b77525b62e0dbdb3dae344f660b0f9f8f63ca512d30cd9fa91be8b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "57c66c318a5615f8a519c12b40043d971e39b8b236dcdbf035ba937cb04a6aca.npz",
      "sha256": "605ba301d95d6bc6a5e89e54a1ecab325be8b5ec6b5cf2ce970a300a4c009ac6",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.24.post_feedforward_layernorm.weight": {
      "base_sha256": "f90c30e774400f0a9eebd22d9220c281cde9db95366069119c4d09de860b0237",
      "changed": 2560,
      "content_sha256": "db4d9a5c6d541b899c5627067ee68b5a09de5e957a5aedcc3abd001e0bdcbc4b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0b1d6a382a000d64a01657b474a1e957b25748778db048ee42b59031e7693cd1.npz",
      "sha256": "8db72caf8b04c2d037981f1d663dee0be47035b9c1a15069e4cd1e668777b051",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.25.post_feedforward_layernorm.weight": {
      "base_sha256": "aaeebabe1fa818fe3388ded46efca3b2fcfe87049a70d1285411b23092793000",
      "changed": 2560,
      "content_sha256": "ff3f52bee99300b77be32d7b721fbf00edf47351be10e19ded9a4f9d3cb6b01d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "574a6b7ff84afdfdcfe2f010f66f879e6f9c8dc040987c39b43a0f3efada7203.npz",
      "sha256": "e8bfdcca46b03741afa716c64836420d38655a45e901637089f2892e312043a8",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.26.post_feedforward_layernorm.weight": {
      "base_sha256": "cd1d93d680e66e0c5649f4079d22f6afaca373da9d4f0df0c981b9e2273196aa",
      "changed": 2560,
      "content_sha256": "7e3efbf40291e8c8a2c0bcf1021e759cc0c199acb9ce1ddbcaaf41f8d9055593",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "af4c62bf12cd54912be9139e6e3992ff89db2aa89b3893fac489c2fbf1ceb48e.npz",
      "sha256": "910a243dc21d4be21e016b27fc0795442449ee149e557fda442756f2860285d3",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.27.post_feedforward_layernorm.weight": {
      "base_sha256": "0a0191055a177497217a5301b209bf912d04361bf09fcc934686406671142058",
      "changed": 2560,
      "content_sha256": "c54cea6aecd18d064d397bc1b4cc2cb9b5d484d4ada8526bcf67e2e8d011a362",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c01d30cf50acff3982f1344d5b19830e6021a1be84945b613a0e770a2783d9cd.npz",
      "sha256": "d41ed573d8fe661df5babb4263a97795ea52e88b37bd1c7e6d6269bb8dba2d40",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.28.post_feedforward_layernorm.weight": {
      "base_sha256": "5db6d15e40b990711ed9aa0552a195bd76eed7c5074cab2737ab13a8846e5038",
      "changed": 2560,
      "content_sha256": "63b32b69aec670df8a812d285fe6f39d061daad6bc67d08c755c4f5154f73d30",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9d7633e008ec94a56b6423be08fb87a8a04b57f4b061b97206d1a032ca1429a8.npz",
      "sha256": "71722284f723a1a9d97054096269b7d2dddd4c8609913035f6b8bfd7f73904b5",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.29.post_feedforward_layernorm.weight": {
      "base_sha256": "3c9b3122d708a2d60b44c233d10998d8e7b7c7ac6ea38cd836d7316ba2fd8972",
      "changed": 2560,
      "content_sha256": "818ca131fcfb3ba90fbf86a5155c771b02d169b6274e06ba083ec729ff771704",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "fa92473f5909de0227e5424a048e4bae0f313ba4a902991b75b39057753da0dd.npz",
      "sha256": "81e106456c54d335bb02e2f1d53cfdb6d2272a82fcae97a298f1053928249407",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.30.post_feedforward_layernorm.weight": {
      "base_sha256": "3b1038978f803988e5e6de2d5ddb2e696cbe84558b39f8645405a7bfa1ee50f3",
      "changed": 2560,
      "content_sha256": "184439e9fc5475f043005ca477bd33c8244b948aa0020b4653e3abc075816713",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c7195d7bbbf3ec90680d4cd156699f0ad9b611d9ddfc78b684046d1f6dc21c84.npz",
      "sha256": "0c69d170d72c086e1a070aefccecc37177df2de550f71b652e6e3c337288f4b8",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.31.post_feedforward_layernorm.weight": {
      "base_sha256": "25e5d11534379bcf874a73d739c8c47d4077ad2e66cac4ac99e0891bb1758f15",
      "changed": 2560,
      "content_sha256": "5ad79c2a314dd118b44731697f609ab14e7ae2b87b2fa5cb7059a58da24792be",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "822f1a8b17a51a9a82e221e664c005431e34783377660f9afbd7d10e0ef96992.npz",
      "sha256": "c6e01ff8928834a90bd18c9002c56f1b2249fcb0c1603b550074e1f6f7e471a2",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.32.post_feedforward_layernorm.weight": {
      "base_sha256": "1f490a1004857564bd05c5a631b0b5a6b40b7564042225a9a8ec65e1992e4476",
      "changed": 2560,
      "content_sha256": "f235e439f1ecad02294631c97d7b4e1e01f2d6f632beea86833361d92727a249",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "034e0acb9ca8b3bda13b3312468db3d84010807a503c4f61341b0d469032c067.npz",
      "sha256": "839afa3ba855029cab1a51bc224e73ee1ed30d6c732bb6903f27dc99f9132d5d",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 2560,
      "content_sha256": "4527503aee599f44b10156ecb32a4f92c51bc2cb802e2386658177f3a2f1524a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "4d10d981c6f1dc699592b2f9dc6203f6637d5786ea06a138dbecc70dcb8fcbce",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-2004fb1f5ec2486fdc14df5fb5cf04396b6fb0fbe4a12b31d037a9a9f7bfb6d0",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.43103448275862066,
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
        "correct": 40,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.1724137931034483,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第11轮

**当时目的与操作理由（原文）**

Candidate 11: W0-based post-feed-forward effective gain 1.05 in layers 11–22 only, restoring layers 23–33. Compare middle versus late depth after candidate 10 became eligible through one repaired ordinary total count, with no subset accuracy gain. No training or fitted channel selection.

**本轮原记录的主分数**：`0.1724137931034483`；保留原始0–1尺度。

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
  "changed_scalars": 30714,
  "id": "c-c4ea02ff64e0fb30146b25d46622180eac5e462f7a3f930082f4a4ef9a94c95e",
  "l2": 395.5079289615601,
  "parent": "c-2004fb1f5ec2486fdc14df5fb5cf04396b6fb0fbe4a12b31d037a9a9f7bfb6d0",
  "rationale": "Candidate 11: W0-based post-feed-forward effective gain 1.05 in layers 11–22 only, restoring layers 23–33. Compare middle versus late depth after candidate 10 became eligible through one repaired ordinary total count, with no subset accuracy gain. No training or fitted channel selection.",
  "tensors": {
    "language_model.model.layers.11.post_feedforward_layernorm.weight": {
      "base_sha256": "89d384f0b663a59798d0caf3817acf749d1286ee7fa658a800e45949f2bf9d2c",
      "changed": 2560,
      "content_sha256": "a851d956287651329e5de178ad583fcd154c8d2e718debedaa119035f6b60afa",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "33d2fe715bbaf79c665524c2c134192d6c81f83225430f58ac440f64aea9d0a6.npz",
      "sha256": "e8534ce4dc8a324a64f1a55ad54f30e9c62f66dbb8f7bd3562fdb061c4727b8e",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.12.post_feedforward_layernorm.weight": {
      "base_sha256": "f04a87a55283cc720a8ed1ea93c3ea3e3998176474beb56db26e85dcdd82fbee",
      "changed": 2559,
      "content_sha256": "f7f15bd6af8f1b196291e168d550003e25a8972e6bc0e110fa486b59ffa29282",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "364856f727b13766a6dfe092412499e3804b1779e79a98d5d17f571f785f01b0.npz",
      "sha256": "1df1eb0659363725648a2d33ecdb74462bb2a6c3a16851c30a8de2a681260e54",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.13.post_feedforward_layernorm.weight": {
      "base_sha256": "f595e44e15f2081870bdfabfe3cd8aef4c5e22bc5f0000b595d59e401df29de3",
      "changed": 2560,
      "content_sha256": "97c4028df7129f922e8043f4d247714fed4ec469dc92b933c3465b3065f627e0",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "55908453b2eaf90446af4573a8423cf9ca877947369821efec861e6d5152b13f.npz",
      "sha256": "f51f983ddb508b47a9069b3fd4d623226d5c0028a483906fb46dedc42808afca",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.14.post_feedforward_layernorm.weight": {
      "base_sha256": "f4ab4a625f4d59c621557cf3f253fbf7c265bf356d1dd97604a6544d49895af5",
      "changed": 2558,
      "content_sha256": "222771a961a73c37abe15e50bca27428b0f5cfee941736281215c1773c6fcb0d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0ff4502ecd17ade201c3be3ba5bd899c24748fe17975d199c57a4d29ad1beae8.npz",
      "sha256": "ce39d7b2b8f3ba450de2690d54d2bb6dd3d5cda801e1f257295e03297f9be41a",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.15.post_feedforward_layernorm.weight": {
      "base_sha256": "c3a0ecc631fc86eeaa78e7d6351f2659cebf1132b856183277b448f8db983d4f",
      "changed": 2560,
      "content_sha256": "559079360d617d908ffe95118f7444e7030c447ddb753abb4cca983848248054",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "bee0d6867067a9e42d89014f4d3d7bb008f720190fdd6f0d9ba6bc41cdd817c5.npz",
      "sha256": "5af9d3b3e923a19d1b4da8b913cf65d1fb221dd3e0473cf7d13482436bb3fbe6",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.16.post_feedforward_layernorm.weight": {
      "base_sha256": "83b002dc6701177b1aa90dac5d981fe3cf205a63210de97a2759e071b22afa99",
      "changed": 2560,
      "content_sha256": "2cd73ba02bda1008a37bb65d53669f4831067dd37eb1f8005e721875920d40da",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "ccc477cd6b70843cc0218c101088bfdab11a1f3af23336a1df20fae85f1c8c6e.npz",
      "sha256": "165ff4c23be74fbd70336546943116757c1565a23e2db49c19a1afe5717a25e4",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.17.post_feedforward_layernorm.weight": {
      "base_sha256": "909c707fd7898fe36b26ffdc0e92d398396ffb50c4872e5f9744236bf6ff5cf5",
      "changed": 2559,
      "content_sha256": "0e7eda7dc75f04fdf0873586a4d7afe88cb92c9cfeebf2aac2a4c15836ec6b27",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d8b3d19f20e2571c310c49349cbb35a2c53b9ed9c8b5d30402480fade61e834e.npz",
      "sha256": "23a9fb099ea2da38c43036ae06ba9e548324de863c5b9fa38c238b3f390ff059",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.18.post_feedforward_layernorm.weight": {
      "base_sha256": "3c327b7611f24a32db3b90b669bd356334cfdf090ee8764270740d7508343ab1",
      "changed": 2560,
      "content_sha256": "5aa78c7684f5133e7285ea090a9713147f1f713333447922e0961ea8e818c677",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "8ed52067aa07c8b327c623b80134363abfd6a81df9d14180f5bc7b91eec6fbae.npz",
      "sha256": "27ee06e1e56099b1c959edf9cfb3481968ee3e748e86d87306d7a398084f9a98",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.19.post_feedforward_layernorm.weight": {
      "base_sha256": "75e2c5e42d4281a971e80deda155f315db6255451a85e89d3f54ee596a941348",
      "changed": 2560,
      "content_sha256": "d8acccc32af1ffcb9fa17d4b8cdb5cb21ccadd01e91b9f72c46817d44865bacd",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "3068acd71bc65d5ccee8aa09feca75616b331b4c2253cc6f39ba58bf782c1c2e.npz",
      "sha256": "ea789a1c41a136459c9eb73ef331cd7666ded986982c8dff17785a903045a08a",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.20.post_feedforward_layernorm.weight": {
      "base_sha256": "ea4337780feb9cf656408c00a4c19fd4e030dc9e8603c6133ae604bd4c6182c7",
      "changed": 2559,
      "content_sha256": "747419b02b0687686c391a2c012394af5b158b7f35e274fef0217c98efda49f3",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "be40af36f5e417b31fa9c0471fd7149391688a81381abf90817dfe4cc9294e71.npz",
      "sha256": "e2ca31065b4303540a860798c0ac6c58c997867a1c9fb2ea607255cedd9f644e",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.21.post_feedforward_layernorm.weight": {
      "base_sha256": "cbdc7a1f8b9a39fa3ae80c6e4d3afda42f54b3546f260838ffdc7043af8dee52",
      "changed": 2560,
      "content_sha256": "f8787f49ad8d7012e91f883cd1d4611eb8fe6bf5e17f0c2a093fa7bdbebd973b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "f8592e6c92b4d4951711f65302256615871212292c857b97d8416b52855d3c8a.npz",
      "sha256": "cefb6dcc16ea213854ed5db5bab2218e069bb23a009447bdaaef0e94c6e02368",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.22.post_feedforward_layernorm.weight": {
      "base_sha256": "7efbd4f118b8c50bb05627be77c5b4e7b65fb5b01e1771397497adb07087a29f",
      "changed": 2559,
      "content_sha256": "3275ff87c511df381c83d217d56b68de7f2590a862b5047c798930e9b4f40bef",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9b59f2432e6e5ff909e104077ee8b7bffba0d31a2c125d70280eb9f7aba4eab7.npz",
      "sha256": "d3a8cfec7c3922f6aba8b3f7cc46812710979d19eddc7c03fd8f7e51e5c97105",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-c4ea02ff64e0fb30146b25d46622180eac5e462f7a3f930082f4a4ef9a94c95e",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.43103448275862066,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 18,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 27,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
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
        "correct": 33,
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
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.1724137931034483,
    "repair_score": 0.1724137931034483,
    "truncated": 3
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第12轮

**当时目的与操作理由（原文）**

Candidate 12: W0-based post-feed-forward effective gain 1.05 in decoder layers 0–10 only, restoring middle-layer edits. Completes coarse early/middle/late localization of the same perturbation. Middle and late edits tied joint correctness but differed substantially in changed responses; no evidence yet of improved empty-spatial-subset handling. No training.

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
  "changed_scalars": 28102,
  "id": "c-dc3d74a6a7e1fd2f52c5f584ce0e2ae0de669dd87242018cd446e88c7d69c24f",
  "l2": 79.21869847014732,
  "parent": "c-c4ea02ff64e0fb30146b25d46622180eac5e462f7a3f930082f4a4ef9a94c95e",
  "rationale": "Candidate 12: W0-based post-feed-forward effective gain 1.05 in decoder layers 0–10 only, restoring middle-layer edits. Completes coarse early/middle/late localization of the same perturbation. Middle and late edits tied joint correctness but differed substantially in changed responses; no evidence yet of improved empty-spatial-subset handling. No training.",
  "tensors": {
    "language_model.model.layers.0.post_feedforward_layernorm.weight": {
      "base_sha256": "4d1ae452b9efcb6e878416337ad5ea9bb74f5128109ba117b1efde7f38c0589e",
      "changed": 2541,
      "content_sha256": "c2fda465a0b609e2f802274e8cae7755f2d76247cda9b470377c93f7bf22d5e2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "5ba727d69136394583fd603b63395a05540ff515454522e9fad8fff136e9ab77.npz",
      "sha256": "2c47013622eb16cd8047d55ee301833f58008a9509257a5f64a7583374a3ba47",
      "shape": [
        2560
      ],
      "stored_coordinates": 2541
    },
    "language_model.model.layers.1.post_feedforward_layernorm.weight": {
      "base_sha256": "34d9e47dcac71d0fad930e7d9e0955af667b643dc3a866c5970ce36d10a4e214",
      "changed": 2555,
      "content_sha256": "92cc8424a3e55d6e98183092e7f32a0c97f1cc904d099e237c89b368a671166d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "3043785de03184f7d69b59c2bbae1def7875c5f86e5ec79bc04560a7e52fac8c.npz",
      "sha256": "97b3cd0255141e99c4f918985dd7598049b93f3cb7bda41506a296afc585e684",
      "shape": [
        2560
      ],
      "stored_coordinates": 2555
    },
    "language_model.model.layers.10.post_feedforward_layernorm.weight": {
      "base_sha256": "af7761db8fb6d65d7a92deced7aa6ed9ab39d59ee3f31efbf19eff7359129043",
      "changed": 2558,
      "content_sha256": "3c9c78b99197609711451c8f1ee458c89162e6f1c8c68c82c5557627997dab24",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "72f7688908dd4021f31f16b0ab7bcd5e283e44fbb3079a8c543be98fec663b29.npz",
      "sha256": "3fc88008768b77665446a2f3d2a44d96fc1c0b4a47d0386903e83268c4ec7fdf",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.2.post_feedforward_layernorm.weight": {
      "base_sha256": "7ba23c6e074a7d6013a6fe21970c0cc9361ed49862e1683934b065042963081d",
      "changed": 2554,
      "content_sha256": "4d473f9692486d9e32ae0850d77200797de21efa474afb231c59a9afea63d9d3",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "d19217b9d6f7f301cc24a4416125918507b5732edcfe54fa1bb83d498316c4ad.npz",
      "sha256": "c5865e4cce3411af6e957196f3bd558955036e1391a67a9b4fe49d54cd2657b0",
      "shape": [
        2560
      ],
      "stored_coordinates": 2554
    },
    "language_model.model.layers.3.post_feedforward_layernorm.weight": {
      "base_sha256": "7cabe9ab9a7858d9c3e94a3e8f66b9f9b94007ab11007c63e2ff7263c5b74383",
      "changed": 2549,
      "content_sha256": "3854a6557436eb26a2caa01024df2b06f849898e3a90ec33b2b5735b427df5e2",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "615261243226abac034054cbbf923da84686df97447bfdd44e26734596fa4258.npz",
      "sha256": "962bfec24adce6c8fd4a68a696fb806d2954e009cf2ed0e873918200c04b6ade",
      "shape": [
        2560
      ],
      "stored_coordinates": 2549
    },
    "language_model.model.layers.4.post_feedforward_layernorm.weight": {
      "base_sha256": "0cbd169db1d4ae9e2c5cd546dae9fe997448c2af2f9ac682c0a368db8274a934",
      "changed": 2557,
      "content_sha256": "165ee08fa799827ad1d2f6a73adab88bb5e61b5bead984960678beccdecc0758",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "47402777e17d78ecc6523e21c921b515e730fc00545f0b66ba6465423c9c1de8.npz",
      "sha256": "b1a757bd6f802df766decc725ad7997ce3b924f04978df75526fe1aaa8eab863",
      "shape": [
        2560
      ],
      "stored_coordinates": 2557
    },
    "language_model.model.layers.5.post_feedforward_layernorm.weight": {
      "base_sha256": "50d2b10526e4e98e53be4e791087ccf1b8f00b14065981a8480d4707705eab85",
      "changed": 2556,
      "content_sha256": "51e416242dc58eeb5ae1105fa091b12224f9b68f1ac5ca0ab7fcbf6177aee90f",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "721cf796c77ca19da54e1fadac9a960f3b191367320b198173d870a75e9fccf6.npz",
      "sha256": "cbd48c7699be273272d93a3dc054e8c294a61154344dea53be3986f8efa9ebd3",
      "shape": [
        2560
      ],
      "stored_coordinates": 2556
    },
    "language_model.model.layers.6.post_feedforward_layernorm.weight": {
      "base_sha256": "7a12e34412b076f6131e31747ab5396751f334b3fd00192be608f83e9db86051",
      "changed": 2558,
      "content_sha256": "506881917179204eeadbb17599eceb8e27a0fb03e507be80354f18b7d22a315e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "5dc5b2fd489c100c79bb238ad3b2e65e26153847eaf5c19b10bd8b413992d67e.npz",
      "sha256": "2559588be83dee3c44888cb0ce3bff0fb2286c764a74334f4fff192c5c051be9",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.7.post_feedforward_layernorm.weight": {
      "base_sha256": "4047ab8dd31dc5fe079ad664f9e9b9d1b224ede91a5bd71432cc6e1343d5ca86",
      "changed": 2558,
      "content_sha256": "b3becbaa4fe62f58eede3f4a8136eee9f36351e685190022ff5505e33d1e043e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "b2542d99a990ca2076dceec5b257ba9f32acb35aa0b4e4f45ff206dcb6313e49.npz",
      "sha256": "422f32ab8f8247daf137fbaed33198ddda7aaf32e02e272c5f3fe1b31631c9d1",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.8.post_feedforward_layernorm.weight": {
      "base_sha256": "b0494c300d1bf8aeb1054b693e119bb4e046b3b1e39b302c9aa51648b4614f46",
      "changed": 2558,
      "content_sha256": "58b7defcfa0358c6c691f890e598e8b1b111dab531defab9521c1808e322c7ec",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "4fdd0090a05f653dbc385da916a94c0f8e60b6fef947c4dcf6aaa8d6344ac18a.npz",
      "sha256": "560329805c771aaae5b87db3ea03b3bd03b5cf87fd3201f5cebda0c5be87aacb",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    },
    "language_model.model.layers.9.post_feedforward_layernorm.weight": {
      "base_sha256": "26c6490dfd39ca7b613f8bf76ae4f3afc029c9ff89a1032f0b9f70d19df4980e",
      "changed": 2558,
      "content_sha256": "2e0830a5545313f3578c07c732a0710be9fef7f54b1f45c1e4428d534ef42aeb",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0c8e013044212b7472539090ce5481b7e2a763cfcb21d33d800f1e92faaf0830.npz",
      "sha256": "cd78a71b77dceef4e5e110b46899fe8e71fbd9711d5ebbc9c7a906b57ddede8f",
      "shape": [
        2560
      ],
      "stored_coordinates": 2558
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-dc3d74a6a7e1fd2f52c5f584ce0e2ae0de669dd87242018cd446e88c7d69c24f",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.41594827586206895,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 16,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 26,
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
        "correct": 18,
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
        "correct": 38,
        "n": 58
      }
    },
    "format_errors": 9,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第13轮

**当时目的与操作理由（原文）**

Candidate 13: restore decoder norm edits to W0 and multiply only tied embedding/lm_head row 236771 (digit zero) by 1.5. Scalar motivated by the earlier fork zero-logit gap; development labels used to diagnose expected true/false-zero tradeoffs, not to fit a classifier or train the model. W0 input sequences contain no zero token. This tests output calibration, not established spatial reasoning repair; subsequent generated-token effects and BF16 rounding require full evaluation.

**本轮原记录的主分数**：`0.20689655172413793`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-334768167d2355dda8d84fcb0093a22e3a4baed8fb7d16795cbb88419b0b44d4",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.20689655172413793
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 2560,
  "id": "c-334768167d2355dda8d84fcb0093a22e3a4baed8fb7d16795cbb88419b0b44d4",
  "l2": 0.5131917003244372,
  "parent": "c-dc3d74a6a7e1fd2f52c5f584ce0e2ae0de669dd87242018cd446e88c7d69c24f",
  "rationale": "Candidate 13: restore decoder norm edits to W0 and multiply only tied embedding/lm_head row 236771 (digit zero) by 1.5. Scalar motivated by the earlier fork zero-logit gap; development labels used to diagnose expected true/false-zero tradeoffs, not to fit a classifier or train the model. W0 input sequences contain no zero token. This tests output calibration, not established spatial reasoning repair; subsequent generated-token effects and BF16 rounding require full evaluation.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "a996d57f48ce85462e123e29d21341a631b7f7c860cf0e37d378bf695570325d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "8cfc48f0fe8181a081f36c4563f7cceef54d3ea4b3f2a2aa0c953bf537d80895",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-334768167d2355dda8d84fcb0093a22e3a4baed8fb7d16795cbb88419b0b44d4",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4547413793103448,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 28,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 23,
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
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 23,
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
    "primary_joint": 0.1896551724137931,
    "repair_score": 0.20689655172413793,
    "truncated": 3
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第14轮

**当时目的与操作理由（原文）**

Candidate 14: W0-based tied embedding/lm_head zero-token row 236771 scaled by 1.35, with all other parameters at W0. Candidate 13 at 1.50 improved ordinary joint correctness but produced false zeros and a repeated-zero truncation. Test whether a smaller gain reduces these side effects, potentially sacrificing empty-subset repairs. Development-guided output calibration, not training or an established spatial-reasoning repair.

**本轮原记录的主分数**：`0.1810344827586207`；保留原始0–1尺度。

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
  "changed_scalars": 2560,
  "id": "c-7331cfe30d0aaf6181801f966761a02c165a62ee76bbed1bc3757d226d32c115",
  "l2": 0.35883087055957835,
  "parent": "c-334768167d2355dda8d84fcb0093a22e3a4baed8fb7d16795cbb88419b0b44d4",
  "rationale": "Candidate 14: W0-based tied embedding/lm_head zero-token row 236771 scaled by 1.35, with all other parameters at W0. Candidate 13 at 1.50 improved ordinary joint correctness but produced false zeros and a repeated-zero truncation. Test whether a smaller gain reduces these side effects, potentially sacrificing empty-subset repairs. Development-guided output calibration, not training or an established spatial-reasoning repair.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "c7e36f11fffad528bb403eeda36e2e64af2e4049cd4ea4b2bd89c570f13b8004",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "71f3f4665c7d03fc960ae239f2b6a34f000f030e9232c160e7952d21f25ea056",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-7331cfe30d0aaf6181801f966761a02c165a62ee76bbed1bc3757d226d32c115",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.44396551724137934,
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
        "correct": 20,
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
        "correct": 22,
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
    "repair_score": 0.1810344827586207,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第15轮

**当时目的与操作理由（原文）**

Candidate 15: independently W0-based zero-token tied embedding/lm_head row 236771 scaled by 1.65; all other parameters unchanged. Complements gains 1.35 and 1.50 to characterize the calibration tradeoff. The lower gain reduced false zeros and numeric repetition but retained fewer empty-subset repairs. Higher gain may recover additional empty subsets while worsening nonempty counts or generation stability. Development-guided scalar exploration, without training or claims of repaired spatial computation.

**本轮原记录的主分数**：`0.20689655172413793`；保留原始0–1尺度。

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
  "changed_scalars": 2560,
  "id": "c-c231bcf36432459301a55cfcfceb15fed05862f43f8968a5494cb45b703158c9",
  "l2": 0.6667929691503854,
  "parent": "c-7331cfe30d0aaf6181801f966761a02c165a62ee76bbed1bc3757d226d32c115",
  "rationale": "Candidate 15: independently W0-based zero-token tied embedding/lm_head row 236771 scaled by 1.65; all other parameters unchanged. Complements gains 1.35 and 1.50 to characterize the calibration tradeoff. The lower gain reduced false zeros and numeric repetition but retained fewer empty-subset repairs. Higher gain may recover additional empty subsets while worsening nonempty counts or generation stability. Development-guided scalar exploration, without training or claims of repaired spatial computation.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "f8f0a187d5ead8121d43a11f99b70e26ec706d41f13ab1e09093a6bb12800530",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "9cd0a99130e948a8436f66acc2e53588d703d99f6e756c0a636e71cee5424f69",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-c231bcf36432459301a55cfcfceb15fed05862f43f8968a5494cb45b703158c9",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.46120689655172414,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 21,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 26,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 23,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 25,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 21,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 34,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 26,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 38,
        "n": 58
      }
    },
    "format_errors": 3,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.1896551724137931,
    "repair_score": 0.20689655172413793,
    "truncated": 15
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第16轮

**当时目的与操作理由（原文）**

Candidate 16: combine W0-based zero-token row gain 1.50 with effective post_feedforward_layernorm gain 1.05 in decoder layers 23–33; every other parameter remains W0. Tests interaction between candidate 13's zero calibration and candidate 10's small ordinary-total benefit. The stronger zero-only candidate 15 failed truncation and total-count protections, so it is not retained in this combination. No training; benefits are not assumed additive.

**本轮原记录的主分数**：`0.21551724137931033`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-9c34595dd088026f8b103d2bfccb22f4d9a3f0f45bee975f9eb52ec252b4d425",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.21551724137931033
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 30719,
  "id": "c-9c34595dd088026f8b103d2bfccb22f4d9a3f0f45bee975f9eb52ec252b4d425",
  "l2": 1283.6414469063495,
  "parent": "c-c231bcf36432459301a55cfcfceb15fed05862f43f8968a5494cb45b703158c9",
  "rationale": "Candidate 16: combine W0-based zero-token row gain 1.50 with effective post_feedforward_layernorm gain 1.05 in decoder layers 23–33; every other parameter remains W0. Tests interaction between candidate 13's zero calibration and candidate 10's small ordinary-total benefit. The stronger zero-only candidate 15 failed truncation and total-count protections, so it is not retained in this combination. No training; benefits are not assumed additive.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "a996d57f48ce85462e123e29d21341a631b7f7c860cf0e37d378bf695570325d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "8cfc48f0fe8181a081f36c4563f7cceef54d3ea4b3f2a2aa0c953bf537d80895",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.23.post_feedforward_layernorm.weight": {
      "base_sha256": "21cb1dcda168867e6ec841a27b8904b023b9e16b0ffef21d5aa5ae8083e17cf6",
      "changed": 2559,
      "content_sha256": "562d7670e2b77525b62e0dbdb3dae344f660b0f9f8f63ca512d30cd9fa91be8b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "57c66c318a5615f8a519c12b40043d971e39b8b236dcdbf035ba937cb04a6aca.npz",
      "sha256": "605ba301d95d6bc6a5e89e54a1ecab325be8b5ec6b5cf2ce970a300a4c009ac6",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.24.post_feedforward_layernorm.weight": {
      "base_sha256": "f90c30e774400f0a9eebd22d9220c281cde9db95366069119c4d09de860b0237",
      "changed": 2560,
      "content_sha256": "db4d9a5c6d541b899c5627067ee68b5a09de5e957a5aedcc3abd001e0bdcbc4b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0b1d6a382a000d64a01657b474a1e957b25748778db048ee42b59031e7693cd1.npz",
      "sha256": "8db72caf8b04c2d037981f1d663dee0be47035b9c1a15069e4cd1e668777b051",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.25.post_feedforward_layernorm.weight": {
      "base_sha256": "aaeebabe1fa818fe3388ded46efca3b2fcfe87049a70d1285411b23092793000",
      "changed": 2560,
      "content_sha256": "ff3f52bee99300b77be32d7b721fbf00edf47351be10e19ded9a4f9d3cb6b01d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "574a6b7ff84afdfdcfe2f010f66f879e6f9c8dc040987c39b43a0f3efada7203.npz",
      "sha256": "e8bfdcca46b03741afa716c64836420d38655a45e901637089f2892e312043a8",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.26.post_feedforward_layernorm.weight": {
      "base_sha256": "cd1d93d680e66e0c5649f4079d22f6afaca373da9d4f0df0c981b9e2273196aa",
      "changed": 2560,
      "content_sha256": "7e3efbf40291e8c8a2c0bcf1021e759cc0c199acb9ce1ddbcaaf41f8d9055593",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "af4c62bf12cd54912be9139e6e3992ff89db2aa89b3893fac489c2fbf1ceb48e.npz",
      "sha256": "910a243dc21d4be21e016b27fc0795442449ee149e557fda442756f2860285d3",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.27.post_feedforward_layernorm.weight": {
      "base_sha256": "0a0191055a177497217a5301b209bf912d04361bf09fcc934686406671142058",
      "changed": 2560,
      "content_sha256": "c54cea6aecd18d064d397bc1b4cc2cb9b5d484d4ada8526bcf67e2e8d011a362",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c01d30cf50acff3982f1344d5b19830e6021a1be84945b613a0e770a2783d9cd.npz",
      "sha256": "d41ed573d8fe661df5babb4263a97795ea52e88b37bd1c7e6d6269bb8dba2d40",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.28.post_feedforward_layernorm.weight": {
      "base_sha256": "5db6d15e40b990711ed9aa0552a195bd76eed7c5074cab2737ab13a8846e5038",
      "changed": 2560,
      "content_sha256": "63b32b69aec670df8a812d285fe6f39d061daad6bc67d08c755c4f5154f73d30",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9d7633e008ec94a56b6423be08fb87a8a04b57f4b061b97206d1a032ca1429a8.npz",
      "sha256": "71722284f723a1a9d97054096269b7d2dddd4c8609913035f6b8bfd7f73904b5",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.29.post_feedforward_layernorm.weight": {
      "base_sha256": "3c9b3122d708a2d60b44c233d10998d8e7b7c7ac6ea38cd836d7316ba2fd8972",
      "changed": 2560,
      "content_sha256": "818ca131fcfb3ba90fbf86a5155c771b02d169b6274e06ba083ec729ff771704",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "fa92473f5909de0227e5424a048e4bae0f313ba4a902991b75b39057753da0dd.npz",
      "sha256": "81e106456c54d335bb02e2f1d53cfdb6d2272a82fcae97a298f1053928249407",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.30.post_feedforward_layernorm.weight": {
      "base_sha256": "3b1038978f803988e5e6de2d5ddb2e696cbe84558b39f8645405a7bfa1ee50f3",
      "changed": 2560,
      "content_sha256": "184439e9fc5475f043005ca477bd33c8244b948aa0020b4653e3abc075816713",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c7195d7bbbf3ec90680d4cd156699f0ad9b611d9ddfc78b684046d1f6dc21c84.npz",
      "sha256": "0c69d170d72c086e1a070aefccecc37177df2de550f71b652e6e3c337288f4b8",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.31.post_feedforward_layernorm.weight": {
      "base_sha256": "25e5d11534379bcf874a73d739c8c47d4077ad2e66cac4ac99e0891bb1758f15",
      "changed": 2560,
      "content_sha256": "5ad79c2a314dd118b44731697f609ab14e7ae2b87b2fa5cb7059a58da24792be",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "822f1a8b17a51a9a82e221e664c005431e34783377660f9afbd7d10e0ef96992.npz",
      "sha256": "c6e01ff8928834a90bd18c9002c56f1b2249fcb0c1603b550074e1f6f7e471a2",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.32.post_feedforward_layernorm.weight": {
      "base_sha256": "1f490a1004857564bd05c5a631b0b5a6b40b7564042225a9a8ec65e1992e4476",
      "changed": 2560,
      "content_sha256": "f235e439f1ecad02294631c97d7b4e1e01f2d6f632beea86833361d92727a249",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "034e0acb9ca8b3bda13b3312468db3d84010807a503c4f61341b0d469032c067.npz",
      "sha256": "839afa3ba855029cab1a51bc224e73ee1ed30d6c732bb6903f27dc99f9132d5d",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 2560,
      "content_sha256": "4527503aee599f44b10156ecb32a4f92c51bc2cb802e2386658177f3a2f1524a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "4d10d981c6f1dc699592b2f9dc6203f6637d5786ea06a138dbecc70dcb8fcbce",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-9c34595dd088026f8b103d2bfccb22f4d9a3f0f45bee975f9eb52ec252b4d425",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4504310344827586,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 27,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 23,
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
        "correct": 33,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 23,
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
    "primary_joint": 0.1896551724137931,
    "repair_score": 0.21551724137931033,
    "truncated": 4
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第17轮

**当时目的与操作理由（原文）**

Candidate 17: W0-based zero-token tied row gain 1.50 plus visual-bridge mm_soft_emb_norm effective gain 0.90; restore all decoder norm edits to W0. Candidate 2's bridge attenuation modestly improved overall accuracy without improving ordinary joint correctness. Test its interaction with candidate 13's zero calibration, separately from the late-layer combination. No training or fitted channel ranking; all outcomes require full development evaluation.

**本轮原记录的主分数**：`0.21551724137931033`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-b77d500cbd51c5a107504d55674393523ea267e4155035cce6e273965d942795",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.21551724137931033
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 3707,
  "id": "c-b77d500cbd51c5a107504d55674393523ea267e4155035cce6e273965d942795",
  "l2": 3.696797782616449,
  "parent": "c-9c34595dd088026f8b103d2bfccb22f4d9a3f0f45bee975f9eb52ec252b4d425",
  "rationale": "Candidate 17: W0-based zero-token tied row gain 1.50 plus visual-bridge mm_soft_emb_norm effective gain 0.90; restore all decoder norm edits to W0. Candidate 2's bridge attenuation modestly improved overall accuracy without improving ordinary joint correctness. Test its interaction with candidate 13's zero calibration, separately from the late-layer combination. No training or fitted channel ranking; all outcomes require full development evaluation.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "a996d57f48ce85462e123e29d21341a631b7f7c860cf0e37d378bf695570325d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "8cfc48f0fe8181a081f36c4563f7cceef54d3ea4b3f2a2aa0c953bf537d80895",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "2cf06d47aaee6afbfe3fd749531c1b0c50837eae4877c7a473fb1c5e351f5244",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "45266f873a7f1dc3f20faa2897302906ddde001934f7e3c4e2c58ee84e7c1dbf",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-b77d500cbd51c5a107504d55674393523ea267e4155035cce6e273965d942795",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.46551724137931033,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 24,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 22,
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
    "primary_joint": 0.1896551724137931,
    "repair_score": 0.21551724137931033,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第18轮

**当时目的与操作理由（原文）**

Candidate 18: retain candidate 17's W0-based zero-row gain 1.50 and visual-bridge effective gain 0.90, adding effective post-feed-forward gain 1.05 only in layers 23–33. Completes the interaction comparison among zero calibration, visual attenuation, and late-layer residual scaling. Candidate 17 tied candidate 16's joint score with fewer parameters and fewer truncations; this test asks whether the late-layer total-count benefit survives visual attenuation without violating protections. No training.

**本轮原记录的主分数**：`0.20689655172413793`；保留原始0–1尺度。

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
  "changed_scalars": 31866,
  "id": "c-7013b048a3d311c60d171b65bcfe5ba148c0a0c9cf8bd10e15c86fe5c984b0a9",
  "l2": 1283.64666757015,
  "parent": "c-b77d500cbd51c5a107504d55674393523ea267e4155035cce6e273965d942795",
  "rationale": "Candidate 18: retain candidate 17's W0-based zero-row gain 1.50 and visual-bridge effective gain 0.90, adding effective post-feed-forward gain 1.05 only in layers 23–33. Completes the interaction comparison among zero calibration, visual attenuation, and late-layer residual scaling. Candidate 17 tied candidate 16's joint score with fewer parameters and fewer truncations; this test asks whether the late-layer total-count benefit survives visual attenuation without violating protections. No training.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "a996d57f48ce85462e123e29d21341a631b7f7c860cf0e37d378bf695570325d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "8cfc48f0fe8181a081f36c4563f7cceef54d3ea4b3f2a2aa0c953bf537d80895",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.23.post_feedforward_layernorm.weight": {
      "base_sha256": "21cb1dcda168867e6ec841a27b8904b023b9e16b0ffef21d5aa5ae8083e17cf6",
      "changed": 2559,
      "content_sha256": "562d7670e2b77525b62e0dbdb3dae344f660b0f9f8f63ca512d30cd9fa91be8b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "57c66c318a5615f8a519c12b40043d971e39b8b236dcdbf035ba937cb04a6aca.npz",
      "sha256": "605ba301d95d6bc6a5e89e54a1ecab325be8b5ec6b5cf2ce970a300a4c009ac6",
      "shape": [
        2560
      ],
      "stored_coordinates": 2559
    },
    "language_model.model.layers.24.post_feedforward_layernorm.weight": {
      "base_sha256": "f90c30e774400f0a9eebd22d9220c281cde9db95366069119c4d09de860b0237",
      "changed": 2560,
      "content_sha256": "db4d9a5c6d541b899c5627067ee68b5a09de5e957a5aedcc3abd001e0bdcbc4b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "0b1d6a382a000d64a01657b474a1e957b25748778db048ee42b59031e7693cd1.npz",
      "sha256": "8db72caf8b04c2d037981f1d663dee0be47035b9c1a15069e4cd1e668777b051",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.25.post_feedforward_layernorm.weight": {
      "base_sha256": "aaeebabe1fa818fe3388ded46efca3b2fcfe87049a70d1285411b23092793000",
      "changed": 2560,
      "content_sha256": "ff3f52bee99300b77be32d7b721fbf00edf47351be10e19ded9a4f9d3cb6b01d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "574a6b7ff84afdfdcfe2f010f66f879e6f9c8dc040987c39b43a0f3efada7203.npz",
      "sha256": "e8bfdcca46b03741afa716c64836420d38655a45e901637089f2892e312043a8",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.26.post_feedforward_layernorm.weight": {
      "base_sha256": "cd1d93d680e66e0c5649f4079d22f6afaca373da9d4f0df0c981b9e2273196aa",
      "changed": 2560,
      "content_sha256": "7e3efbf40291e8c8a2c0bcf1021e759cc0c199acb9ce1ddbcaaf41f8d9055593",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "af4c62bf12cd54912be9139e6e3992ff89db2aa89b3893fac489c2fbf1ceb48e.npz",
      "sha256": "910a243dc21d4be21e016b27fc0795442449ee149e557fda442756f2860285d3",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.27.post_feedforward_layernorm.weight": {
      "base_sha256": "0a0191055a177497217a5301b209bf912d04361bf09fcc934686406671142058",
      "changed": 2560,
      "content_sha256": "c54cea6aecd18d064d397bc1b4cc2cb9b5d484d4ada8526bcf67e2e8d011a362",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c01d30cf50acff3982f1344d5b19830e6021a1be84945b613a0e770a2783d9cd.npz",
      "sha256": "d41ed573d8fe661df5babb4263a97795ea52e88b37bd1c7e6d6269bb8dba2d40",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.28.post_feedforward_layernorm.weight": {
      "base_sha256": "5db6d15e40b990711ed9aa0552a195bd76eed7c5074cab2737ab13a8846e5038",
      "changed": 2560,
      "content_sha256": "63b32b69aec670df8a812d285fe6f39d061daad6bc67d08c755c4f5154f73d30",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "9d7633e008ec94a56b6423be08fb87a8a04b57f4b061b97206d1a032ca1429a8.npz",
      "sha256": "71722284f723a1a9d97054096269b7d2dddd4c8609913035f6b8bfd7f73904b5",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.29.post_feedforward_layernorm.weight": {
      "base_sha256": "3c9b3122d708a2d60b44c233d10998d8e7b7c7ac6ea38cd836d7316ba2fd8972",
      "changed": 2560,
      "content_sha256": "818ca131fcfb3ba90fbf86a5155c771b02d169b6274e06ba083ec729ff771704",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "fa92473f5909de0227e5424a048e4bae0f313ba4a902991b75b39057753da0dd.npz",
      "sha256": "81e106456c54d335bb02e2f1d53cfdb6d2272a82fcae97a298f1053928249407",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.30.post_feedforward_layernorm.weight": {
      "base_sha256": "3b1038978f803988e5e6de2d5ddb2e696cbe84558b39f8645405a7bfa1ee50f3",
      "changed": 2560,
      "content_sha256": "184439e9fc5475f043005ca477bd33c8244b948aa0020b4653e3abc075816713",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "c7195d7bbbf3ec90680d4cd156699f0ad9b611d9ddfc78b684046d1f6dc21c84.npz",
      "sha256": "0c69d170d72c086e1a070aefccecc37177df2de550f71b652e6e3c337288f4b8",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.31.post_feedforward_layernorm.weight": {
      "base_sha256": "25e5d11534379bcf874a73d739c8c47d4077ad2e66cac4ac99e0891bb1758f15",
      "changed": 2560,
      "content_sha256": "5ad79c2a314dd118b44731697f609ab14e7ae2b87b2fa5cb7059a58da24792be",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "822f1a8b17a51a9a82e221e664c005431e34783377660f9afbd7d10e0ef96992.npz",
      "sha256": "c6e01ff8928834a90bd18c9002c56f1b2249fcb0c1603b550074e1f6f7e471a2",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.32.post_feedforward_layernorm.weight": {
      "base_sha256": "1f490a1004857564bd05c5a631b0b5a6b40b7564042225a9a8ec65e1992e4476",
      "changed": 2560,
      "content_sha256": "f235e439f1ecad02294631c97d7b4e1e01f2d6f632beea86833361d92727a249",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "034e0acb9ca8b3bda13b3312468db3d84010807a503c4f61341b0d469032c067.npz",
      "sha256": "839afa3ba855029cab1a51bc224e73ee1ed30d6c732bb6903f27dc99f9132d5d",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "language_model.model.layers.33.post_feedforward_layernorm.weight": {
      "base_sha256": "074f3c02938721ea0da67160cbc9277954660d6473026f9ef7b6c9a506770044",
      "changed": 2560,
      "content_sha256": "4527503aee599f44b10156ecb32a4f92c51bc2cb802e2386658177f3a2f1524a",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "469a534e9507b45ce644f5240a96c218e743f2ff6244a7d5ef733da7b332f469.npz",
      "sha256": "4d10d981c6f1dc699592b2f9dc6203f6637d5786ea06a138dbecc70dcb8fcbce",
      "shape": [
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "2cf06d47aaee6afbfe3fd749531c1b0c50837eae4877c7a473fb1c5e351f5244",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "45266f873a7f1dc3f20faa2897302906ddde001934f7e3c4e2c58ee84e7c1dbf",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-7013b048a3d311c60d171b65bcfe5ba148c0a0c9cf8bd10e15c86fe5c984b0a9",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.46120689655172414,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 28,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 23,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 23,
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
    "primary_joint": 0.1896551724137931,
    "repair_score": 0.20689655172413793,
    "truncated": 5
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第19轮

**当时目的与操作理由（原文）**

Candidate 19: W0-based effective mm_soft_emb_norm gain 0.80 on 144 channels with the highest spatial-mean energy fraction, selected without labels from eight fixed, evenly spaced development images. Channel sets and statistics are recorded in turn-0091; three zero-energy channels were excluded. All embedding and decoder edits are restored to W0. Tests selective attenuation of spatially homogeneous bridge features, not an established nuisance or spatial-reasoning mechanism. The planned low-fraction control is channel-count matched, not energy matched. No training.

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
  "changed_scalars": 143,
  "id": "c-9e28b2456d6d04d8a1beb8114c7950832ae75f055eca868540f6049932968d07",
  "l2": 2.5101706259684162,
  "parent": "c-7013b048a3d311c60d171b65bcfe5ba148c0a0c9cf8bd10e15c86fe5c984b0a9",
  "rationale": "Candidate 19: W0-based effective mm_soft_emb_norm gain 0.80 on 144 channels with the highest spatial-mean energy fraction, selected without labels from eight fixed, evenly spaced development images. Channel sets and statistics are recorded in turn-0091; three zero-energy channels were excluded. All embedding and decoder edits are restored to W0. Tests selective attenuation of spatially homogeneous bridge features, not an established nuisance or spatial-reasoning mechanism. The planned low-fraction control is channel-count matched, not energy matched. No training.",
  "tensors": {
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 143,
      "content_sha256": "a519e8cfaaa79bf18c32f8896240636fd7792c71fadb4da55036e13ec38bbf0b",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "cb731112cb0ab147ad8d1908bb3b95bb6650943139bf06bb93b9477a5a2b4455",
      "shape": [
        1152
      ],
      "stored_coordinates": 143
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-9e28b2456d6d04d8a1beb8114c7950832ae75f055eca868540f6049932968d07",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4267241379310345,
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
        "correct": 28,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 18,
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
        "correct": 37,
        "n": 58
      }
    },
    "format_errors": 5,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.16379310344827586,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第20轮

**当时目的与操作理由（原文）**

Candidate 20: W0-based effective mm_soft_emb_norm gain 0.80 on the 144 lowest nonzero-energy spatial-mean-fraction channels fixed in turn-0091. Restores candidate 19's high-fraction channels to W0; all other parameters remain W0. This predeclared control matches selected-channel count and gain, but not activation perturbation energy. Candidate 19 did not improve ordinary joint correctness and violated protections despite one empty-spatial repair. No label-based channel ranking or training.

**本轮原记录的主分数**：`0.1724137931034483`；保留原始0–1尺度。

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
  "changed_scalars": 144,
  "id": "c-3896bdd448fd0b86a4ad5f481aa30ef0a973e260088459eed774c3b6a4200ab3",
  "l2": 2.7028389495820058,
  "parent": "c-9e28b2456d6d04d8a1beb8114c7950832ae75f055eca868540f6049932968d07",
  "rationale": "Candidate 20: W0-based effective mm_soft_emb_norm gain 0.80 on the 144 lowest nonzero-energy spatial-mean-fraction channels fixed in turn-0091. Restores candidate 19's high-fraction channels to W0; all other parameters remain W0. This predeclared control matches selected-channel count and gain, but not activation perturbation energy. Candidate 19 did not improve ordinary joint correctness and violated protections despite one empty-spatial repair. No label-based channel ranking or training.",
  "tensors": {
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 144,
      "content_sha256": "e38fb33d83b5a8b51d46c01672b2fbaf829551e5c70286c0e68848b362ec5bfd",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "11f7ffdb23a5bdba934b46e887738c12f3eb459b42034b5d10434101239e4105",
      "shape": [
        1152
      ],
      "stored_coordinates": 144
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-3896bdd448fd0b86a4ad5f481aa30ef0a973e260088459eed774c3b6a4200ab3",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.42887931034482757,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 27,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 18,
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
        "correct": 32,
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
    "repair_score": 0.1724137931034483,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第21轮

**当时目的与操作理由（原文）**

Candidate 21: W0-based effective bridge-norm gain 0.8638117400313101 on the fixed 144 high-spatial-mean-fraction channels, restoring all other channels to W0. The gain equals 1 - 0.2*sqrt(low-set energy/high-set energy), using only the eight W0 captures, and matches candidate 20's predicted squared bridge-output perturbation energy before BF16 rounding. This does not match projected decoder-state or downstream changes. Tests whether candidate 19's harms reflect attenuation strength rather than channel selection. No label-fitted ranking or training.

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
  "changed_scalars": 143,
  "id": "c-5b37f535647132b36eeb789ddb7dccc3976f0a868465f05e0c940ad2d6b98e25",
  "l2": 1.7094913509973446,
  "parent": "c-3896bdd448fd0b86a4ad5f481aa30ef0a973e260088459eed774c3b6a4200ab3",
  "rationale": "Candidate 21: W0-based effective bridge-norm gain 0.8638117400313101 on the fixed 144 high-spatial-mean-fraction channels, restoring all other channels to W0. The gain equals 1 - 0.2*sqrt(low-set energy/high-set energy), using only the eight W0 captures, and matches candidate 20's predicted squared bridge-output perturbation energy before BF16 rounding. This does not match projected decoder-state or downstream changes. Tests whether candidate 19's harms reflect attenuation strength rather than channel selection. No label-fitted ranking or training.",
  "tensors": {
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 143,
      "content_sha256": "0f2ced0816e725f8924e670b3020a2867379ba979dada07cdd8fa03b561f2ad3",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "88d27e4c11f312179f9496c1159b022294d23a0ef402fe3cd9aa0e0bd8eda3ca",
      "shape": [
        1152
      ],
      "stored_coordinates": 143
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-5b37f535647132b36eeb789ddb7dccc3976f0a868465f05e0c940ad2d6b98e25",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
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
        "correct": 28,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 18,
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
        "correct": 36,
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

## 第22轮

**当时目的与操作理由（原文）**

Candidate 22: combine W0-based tied zero-token row gain 1.50 with candidate 21's fixed high-common144 bridge effective gain 0.8638117400313101. Every other parameter remains W0. Tests whether selective visual attenuation interacts differently with output calibration than uniform attenuation did in candidate 17. Candidate 21 alone failed protections and provides no evidence that the selected features are nuisance channels. This is the first of the declared high/low energy-matched interaction pair; no training or assumed additivity.

**本轮原记录的主分数**：`0.1896551724137931`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B1:T1:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 2703,
  "id": "c-5e198bace04e867586215a7dc4cbb6aac9734d260adb1b4c21331092655a3b7c",
  "l2": 1.7848603307868696,
  "parent": "c-5b37f535647132b36eeb789ddb7dccc3976f0a868465f05e0c940ad2d6b98e25",
  "rationale": "Candidate 22: combine W0-based tied zero-token row gain 1.50 with candidate 21's fixed high-common144 bridge effective gain 0.8638117400313101. Every other parameter remains W0. Tests whether selective visual attenuation interacts differently with output calibration than uniform attenuation did in candidate 17. Candidate 21 alone failed protections and provides no evidence that the selected features are nuisance channels. This is the first of the declared high/low energy-matched interaction pair; no training or assumed additivity.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "a996d57f48ce85462e123e29d21341a631b7f7c860cf0e37d378bf695570325d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "8cfc48f0fe8181a081f36c4563f7cceef54d3ea4b3f2a2aa0c953bf537d80895",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 143,
      "content_sha256": "0f2ced0816e725f8924e670b3020a2867379ba979dada07cdd8fa03b561f2ad3",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "88d27e4c11f312179f9496c1159b022294d23a0ef402fe3cd9aa0e0bd8eda3ca",
      "shape": [
        1152
      ],
      "stored_coordinates": 143
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-5e198bace04e867586215a7dc4cbb6aac9734d260adb1b4c21331092655a3b7c",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4353448275862069,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 17,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 27,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 22,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 19,
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
        "correct": 36,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.1896551724137931,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第23轮

**当时目的与操作理由（原文）**

Candidate 23: retain W0-based tied zero-token row gain 1.50, replace the high-common bridge intervention with effective gain 0.80 on the fixed low-common144 channels, and leave all other parameters at W0. Completes the declared interaction comparison with candidate 22 using approximately matched eight-image bridge-output perturbation energy. Candidate 22 failed total-count protection and increased false subset zeros relative to zero-only calibration. No training, label-based channel ranking, or assumed spatial-reasoning repair.

**本轮原记录的主分数**：`0.21551724137931033`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 2704,
  "id": "c-4e6d7177287dda779d425610253f09acdde145eac1f0beb3eba880d18cc6391d",
  "l2": 2.7511277885004626,
  "parent": "c-5e198bace04e867586215a7dc4cbb6aac9734d260adb1b4c21331092655a3b7c",
  "rationale": "Candidate 23: retain W0-based tied zero-token row gain 1.50, replace the high-common bridge intervention with effective gain 0.80 on the fixed low-common144 channels, and leave all other parameters at W0. Completes the declared interaction comparison with candidate 22 using approximately matched eight-image bridge-output perturbation energy. Candidate 22 failed total-count protection and increased false subset zeros relative to zero-only calibration. No training, label-based channel ranking, or assumed spatial-reasoning repair.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "a996d57f48ce85462e123e29d21341a631b7f7c860cf0e37d378bf695570325d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "8cfc48f0fe8181a081f36c4563f7cceef54d3ea4b3f2a2aa0c953bf537d80895",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 144,
      "content_sha256": "e38fb33d83b5a8b51d46c01672b2fbaf829551e5c70286c0e68848b362ec5bfd",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "11f7ffdb23a5bdba934b46e887738c12f3eb459b42034b5d10434101239e4105",
      "shape": [
        1152
      ],
      "stored_coordinates": 144
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-4e6d7177287dda779d425610253f09acdde145eac1f0beb3eba880d18cc6391d",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4482758620689655,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 26,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 23,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 28,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 18,
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
        "correct": 41,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.1896551724137931,
    "repair_score": 0.21551724137931033,
    "truncated": 3
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第24轮

**当时目的与操作理由（原文）**

Candidate 24: W0-based tied zero-token row gain 1.45 plus uniform bridge effective gain 0.90, with all decoder parameters and other embedding rows at W0. First of the seven fixed sensitivity designs recorded in turn-0106. Relative to candidate 17, lowers only the zero gain to test the tradeoff between empty-subset repairs, false zeros, and generation stability. Replaces all selective-channel attenuation. Development-guided scalar exploration, not training or independent validation.

**本轮原记录的主分数**：`0.21551724137931033`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-c20a52e0a986df9c0cccdc5aec965480f0edd044aee46b5243074bf4a6c5ae59",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.21551724137931033
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 3707,
  "id": "c-c20a52e0a986df9c0cccdc5aec965480f0edd044aee46b5243074bf4a6c5ae59",
  "l2": 3.6899703205774994,
  "parent": "c-4e6d7177287dda779d425610253f09acdde145eac1f0beb3eba880d18cc6391d",
  "rationale": "Candidate 24: W0-based tied zero-token row gain 1.45 plus uniform bridge effective gain 0.90, with all decoder parameters and other embedding rows at W0. First of the seven fixed sensitivity designs recorded in turn-0106. Relative to candidate 17, lowers only the zero gain to test the tradeoff between empty-subset repairs, false zeros, and generation stability. Replaces all selective-channel attenuation. Development-guided scalar exploration, not training or independent validation.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "ec4311879f17be61981c13f7cfb59083d373c0f14b90dfb79b5c92ecf5e70d51",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "8718760eada330cc0d99a23b5af8a33e9fd22764c41a60e7afd1f14e2211704b",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "2cf06d47aaee6afbfe3fd749531c1b0c50837eae4877c7a473fb1c5e351f5244",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "45266f873a7f1dc3f20faa2897302906ddde001934f7e3c4e2c58ee84e7c1dbf",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-c20a52e0a986df9c0cccdc5aec965480f0edd044aee46b5243074bf4a6c5ae59",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.46336206896551724,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 30,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 22,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 27,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 21,
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
    "primary_joint": 0.1896551724137931,
    "repair_score": 0.21551724137931033,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第25轮

**当时目的与操作理由（原文）**

Candidate 25: W0-based tied zero-token row 236771 gain 1.55 plus uniform bridge effective gain 0.90; all other embedding rows and decoder parameters remain W0. This is the second sensitivity design fixed in turn-0106. Preserved turn-0109 staging was inspected after authentication recovery and verified in turn-0115 to match the intended BF16-rounded values, with zero embedding changes outside row 236771; no old evaluation was replayed. Tests the empty-subset repair versus false-zero and generation-stability tradeoff relative to gains 1.45 and 1.50. Development-guided scalar exploration, not training or independent validation.

**本轮原记录的主分数**：`0.20689655172413793`；保留原始0–1尺度。

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
  "changed_scalars": 3707,
  "id": "c-5d8f91ca8d72d3eac6aa0b9d4aabf0e9dd5b001e8db8d7585721c3cb1b3dbfdc",
  "l2": 3.7041568820641957,
  "parent": "c-c20a52e0a986df9c0cccdc5aec965480f0edd044aee46b5243074bf4a6c5ae59",
  "rationale": "Candidate 25: W0-based tied zero-token row 236771 gain 1.55 plus uniform bridge effective gain 0.90; all other embedding rows and decoder parameters remain W0. This is the second sensitivity design fixed in turn-0106. Preserved turn-0109 staging was inspected after authentication recovery and verified in turn-0115 to match the intended BF16-rounded values, with zero embedding changes outside row 236771; no old evaluation was replayed. Tests the empty-subset repair versus false-zero and generation-stability tradeoff relative to gains 1.45 and 1.50. Development-guided scalar exploration, not training or independent validation.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "4a751bd8e6270034586952b5303232c241d46bcd6f494c17cb2cff7d7872e804",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "a04abd91f901867519c3602dc3c0990d7563081a18b069c03f8a3174bff4b852",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "2cf06d47aaee6afbfe3fd749531c1b0c50837eae4877c7a473fb1c5e351f5244",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "45266f873a7f1dc3f20faa2897302906ddde001934f7e3c4e2c58ee84e7c1dbf",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-5d8f91ca8d72d3eac6aa0b9d4aabf0e9dd5b001e8db8d7585721c3cb1b3dbfdc",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4676724137931034,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 21,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 23,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 23,
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
    "primary_joint": 0.1896551724137931,
    "repair_score": 0.20689655172413793,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第26轮

**当时目的与操作理由（原文）**

Candidate 26: W0-based tied zero-token row 236771 gain 1.60 plus uniform bridge effective gain 0.90, with all other parameters at W0. Third sensitivity design fixed in turn-0106. Candidate 25 improved overall accuracy and empty-subset responses but reduced ordinary joint correctness relative to candidate 24, increased false zeros, and produced one numeric repetition truncation. This fixed stronger-gain test measures that tradeoff under unchanged full-development protections; no training, independent validation, or presumed spatial-reasoning repair.

**本轮原记录的主分数**：`0.19827586206896552`；保留原始0–1尺度。

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
  "changed_scalars": 3707,
  "id": "c-7428d44c63cbdd49f690d5c1acd253415faf98e091c163148c19b786abe0cfda",
  "l2": 3.712346453855052,
  "parent": "c-5d8f91ca8d72d3eac6aa0b9d4aabf0e9dd5b001e8db8d7585721c3cb1b3dbfdc",
  "rationale": "Candidate 26: W0-based tied zero-token row 236771 gain 1.60 plus uniform bridge effective gain 0.90, with all other parameters at W0. Third sensitivity design fixed in turn-0106. Candidate 25 improved overall accuracy and empty-subset responses but reduced ordinary joint correctness relative to candidate 24, increased false zeros, and produced one numeric repetition truncation. This fixed stronger-gain test measures that tradeoff under unchanged full-development protections; no training, independent validation, or presumed spatial-reasoning repair.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "b6526cbaf2d36047e117fc43d0a37c0b570da11a9ec56388a4fa6a0719658117",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "0cf945dc860bb0c8356bf8c213a23cc24a38eb263c6f1ac2cb751c11e2d9b39d",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "2cf06d47aaee6afbfe3fd749531c1b0c50837eae4877c7a473fb1c5e351f5244",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "45266f873a7f1dc3f20faa2897302906ddde001934f7e3c4e2c58ee84e7c1dbf",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-7428d44c63cbdd49f690d5c1acd253415faf98e091c163148c19b786abe0cfda",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.47413793103448276,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 29,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 24,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 26,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 23,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 24,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 39,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.1724137931034483,
    "repair_score": 0.19827586206896552,
    "truncated": 8
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第27轮

**当时目的与操作理由（原文）**

Candidate 27: W0-based tied zero-token row 236771 gain 1.50 plus uniform bridge effective gain 0.80; every other parameter remains W0. Fourth sensitivity design fixed in turn-0106. Relative to candidate 17, changes only the bridge gain from 0.90 to 0.80. Candidate 26's stronger zero gain failed truncation protection and lowered joint correctness, so this fixed comparison tests bridge attenuation at the lower zero gain without assuming improved spatial reasoning. Development-guided scalar exploration; no training or held-out validation.

**本轮原记录的主分数**：`0.1896551724137931`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 3707,
  "id": "c-a59ae6cee2da442f5dc55199dd97eb5edacf500d0045f6ddcecc9a8db58be17b",
  "l2": 7.339959433040629,
  "parent": "c-7428d44c63cbdd49f690d5c1acd253415faf98e091c163148c19b786abe0cfda",
  "rationale": "Candidate 27: W0-based tied zero-token row 236771 gain 1.50 plus uniform bridge effective gain 0.80; every other parameter remains W0. Fourth sensitivity design fixed in turn-0106. Relative to candidate 17, changes only the bridge gain from 0.90 to 0.80. Candidate 26's stronger zero gain failed truncation protection and lowered joint correctness, so this fixed comparison tests bridge attenuation at the lower zero gain without assuming improved spatial reasoning. Development-guided scalar exploration; no training or held-out validation.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "a996d57f48ce85462e123e29d21341a631b7f7c860cf0e37d378bf695570325d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "8cfc48f0fe8181a081f36c4563f7cceef54d3ea4b3f2a2aa0c953bf537d80895",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "b0c753ca208ad031a3ae259b716ae2d35c9ceae3a7724f08f03f339c8f32eeb4",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "452a8e41bd1ead8124f142da2dee9e74be7ecd66425c2d286e8cef2fb12751b6",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-a59ae6cee2da442f5dc55199dd97eb5edacf500d0045f6ddcecc9a8db58be17b",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.44612068965517243,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 24,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 22,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 25,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 23,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 39,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.1896551724137931,
    "truncated": 3
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第28轮

**当时目的与操作理由（原文）**

Candidate 28: W0-based tied zero-token row 236771 gain 1.50 plus uniform bridge effective gain 0.95; all other parameters remain W0. Fifth sensitivity design fixed in turn-0106. Completes bridge gains 0.80, 0.90, and 0.95 at zero gain 1.50. Candidate 27's stronger attenuation failed B0/T0 total-count protection; this milder setting tests whether gains and harms are dose-sensitive without assuming monotonicity or a spatial-reasoning mechanism. No training or independent validation.

**本轮原记录的主分数**：`0.20689655172413793`；保留原始0–1尺度。

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
  "changed_scalars": 3707,
  "id": "c-79753832e3e8d1fceb3aaf769de2bf3d7ad9efdfe56d82b95b89c274d8214114",
  "l2": 1.9004706192304106,
  "parent": "c-a59ae6cee2da442f5dc55199dd97eb5edacf500d0045f6ddcecc9a8db58be17b",
  "rationale": "Candidate 28: W0-based tied zero-token row 236771 gain 1.50 plus uniform bridge effective gain 0.95; all other parameters remain W0. Fifth sensitivity design fixed in turn-0106. Completes bridge gains 0.80, 0.90, and 0.95 at zero gain 1.50. Candidate 27's stronger attenuation failed B0/T0 total-count protection; this milder setting tests whether gains and harms are dose-sensitive without assuming monotonicity or a spatial-reasoning mechanism. No training or independent validation.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "a996d57f48ce85462e123e29d21341a631b7f7c860cf0e37d378bf695570325d",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "8cfc48f0fe8181a081f36c4563f7cceef54d3ea4b3f2a2aa0c953bf537d80895",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "3c9de258d7d1dca29c24b6793f96fba72a08c20a3f96a37a26eddc1c0d764f4e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "6486d726032982cfd3da44e20d5d6e50f9a4122896fbf85d4fc9e138671184c0",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-79753832e3e8d1fceb3aaf769de2bf3d7ad9efdfe56d82b95b89c274d8214114",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.46120689655172414,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 28,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 23,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 28,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 19,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 21,
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
    "primary_joint": 0.1896551724137931,
    "repair_score": 0.20689655172413793,
    "truncated": 1
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第29轮

**当时目的与操作理由（原文）**

Candidate 29: W0-based tied zero-token row 236771 gain 1.55 plus uniform bridge effective gain 0.80; all other parameters remain W0. Sixth sensitivity design fixed in turn-0106, staged in turn-0127. Compares with candidate 25 at bridge gain 0.90 and candidate 27 at zero gain 1.50. Tests interaction between zero calibration and bridge attenuation, including false zeros, total-count protection, and generation stability. Development-guided scalar exploration; no training, held-out validation, or assumed spatial-reasoning repair.

**本轮原记录的主分数**：`0.1896551724137931`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T0:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-a8a8df63cbfe2a4bfa07bf8ace8660b3758297bf43daf2025fe2f98cb562fc5f",
  "changed_scalars": 3707,
  "id": "c-3a329557d8bea7bc7a7da903ce90b0c2ab981bb3c612ef96429be0187bedb9cf",
  "l2": 7.343668622702671,
  "parent": "c-79753832e3e8d1fceb3aaf769de2bf3d7ad9efdfe56d82b95b89c274d8214114",
  "rationale": "Candidate 29: W0-based tied zero-token row 236771 gain 1.55 plus uniform bridge effective gain 0.80; all other parameters remain W0. Sixth sensitivity design fixed in turn-0106, staged in turn-0127. Compares with candidate 25 at bridge gain 0.90 and candidate 27 at zero gain 1.50. Tests interaction between zero calibration and bridge attenuation, including false zeros, total-count protection, and generation stability. Development-guided scalar exploration; no training, held-out validation, or assumed spatial-reasoning repair.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "4a751bd8e6270034586952b5303232c241d46bcd6f494c17cb2cff7d7872e804",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "a04abd91f901867519c3602dc3c0990d7563081a18b069c03f8a3174bff4b852",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "b0c753ca208ad031a3ae259b716ae2d35c9ceae3a7724f08f03f339c8f32eeb4",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "452a8e41bd1ead8124f142da2dee9e74be7ecd66425c2d286e8cef2fb12751b6",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-3a329557d8bea7bc7a7da903ce90b0c2ab981bb3c612ef96429be0187bedb9cf",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.46120689655172414,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 21,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 24,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 24,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 25,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 22,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 24,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 39,
        "n": 58
      }
    },
    "format_errors": 4,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.15517241379310345,
    "repair_score": 0.1896551724137931,
    "truncated": 4
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第30轮

**当时目的与操作理由（原文）**

Candidate 30: W0-based tied zero-token row 236771 gain 1.55 plus uniform bridge effective gain 0.95; all other parameters remain W0. Final sensitivity design fixed in turn-0106, staged in turn-0130. Completes bridge gains 0.80, 0.90, and 0.95 at zero gain 1.55 and the corresponding comparison with zero gain 1.50. Candidate 29 failed B0/T0 total-count protection despite empty-subset gains. Tests whether milder attenuation preserves joint correctness and generation stability under unchanged evaluation and selection rules. Development-guided scalar exploration, not training or independent validation.

**本轮原记录的主分数**：`0.19827586206896552`；保留原始0–1尺度。

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
  "changed_scalars": 3707,
  "id": "c-39dc0561c1ad0a3169fd862f1a9b449f9d401fadb8aaf34106c885a7c05334ca",
  "l2": 1.914746180553357,
  "parent": "c-3a329557d8bea7bc7a7da903ce90b0c2ab981bb3c612ef96429be0187bedb9cf",
  "rationale": "Candidate 30: W0-based tied zero-token row 236771 gain 1.55 plus uniform bridge effective gain 0.95; all other parameters remain W0. Final sensitivity design fixed in turn-0106, staged in turn-0130. Completes bridge gains 0.80, 0.90, and 0.95 at zero gain 1.55 and the corresponding comparison with zero gain 1.50. Candidate 29 failed B0/T0 total-count protection despite empty-subset gains. Tests whether milder attenuation preserves joint correctness and generation stability under unchanged evaluation and selection rules. Development-guided scalar exploration, not training or independent validation.",
  "tensors": {
    "language_model.model.embed_tokens.weight": {
      "base_sha256": "b33e3f6a89e7345d8735498377d4ceb0d9f09eaa83e911883139d04e0d8b1013",
      "changed": 2560,
      "content_sha256": "4a751bd8e6270034586952b5303232c241d46bcd6f494c17cb2cff7d7872e804",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "7cf1b122be1f8265ad64c83b9a9f1c065e1e780bea0fd1c74ac4598596cb3c69.npz",
      "sha256": "a04abd91f901867519c3602dc3c0990d7563081a18b069c03f8a3174bff4b852",
      "shape": [
        262208,
        2560
      ],
      "stored_coordinates": 2560
    },
    "multi_modal_projector.mm_soft_emb_norm.weight": {
      "base_sha256": "74438a5148912928a40a6fb32d625c76d199327ca2dc136ea3e60ee198736838",
      "changed": 1147,
      "content_sha256": "3c9de258d7d1dca29c24b6793f96fba72a08c20a3f96a37a26eddc1c0d764f4e",
      "dtype": "BF16",
      "encoding": "absolute-f32-sparse-v1",
      "file": "256060d1e6c1680f0e1667b43769562357f1bfd14f0c74e95080f8f92e48afbb.npz",
      "sha256": "6486d726032982cfd3da44e20d5d6e50f9a4122896fbf85d4fc9e138671184c0",
      "shape": [
        1152
      ],
      "stored_coordinates": 1147
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-39dc0561c1ad0a3169fd862f1a9b449f9d401fadb8aaf34106c885a7c05334ca",
  "full_development": true,
  "protocol": "587d794c4fddfb65c3fe2e0862b08000415a54dd3f2735f4b8988994ec23b3b9",
  "summary": {
    "accuracy": 0.4676724137931034,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 28,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 24,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 28,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 20,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 22,
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
    "primary_joint": 0.1724137931034483,
    "repair_score": 0.19827586206896552,
    "truncated": 2
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

