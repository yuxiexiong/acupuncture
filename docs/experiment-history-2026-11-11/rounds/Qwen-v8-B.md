# Qwen-v8-B：逐轮目的、修改与结果

本页逐轮转录已归档值，不重新评分、不运行模型。共50个完整候选；不是新增50次实验。研究者当时的理由按原文保留，其中预期不能读作已验证结果。每轮均从其记录指定的基线和父候选解释，不能默认累加补丁。

原始完整档案（含逐题答案）：

- [experiments/wsp-vlm-open-repair-v8x50-2026-11-05/closeout-evidence.json.gz](https://github.com/yuxiexiong/acupuncture/blob/2ed333ea1e2f4ae2358f081ee37dbaf3c26c6274/experiments/wsp-vlm-open-repair-v8x50-2026-11-05/closeout-evidence.json.gz)

## 第1轮

**当时目的与操作理由（原文）**

Round 1: scale decoder query-normalization weights by 1.10 across all 36 layers. Label-free test of slightly sharper attention for spatial-reference selection; no value, embedding, architecture, prompt, or generation changes. Broad localization screen, not an assumed defective layer.

**本轮原记录的主分数**：`0.5172413793103449`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B1:T0:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 4608,
  "id": "c-f1d3a21809dec3af007a0e3e8d18370751190e3498db47c84c5378f698f8f05d",
  "l2": 11.863296968668552,
  "parent": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "rationale": "Round 1: scale decoder query-normalization weights by 1.10 across all 36 layers. Label-free test of slightly sharper attention for spatial-reference selection; no value, embedding, architecture, prompt, or generation changes. Broad localization screen, not an assumed defective layer.",
  "tensors": {
    "model.language_model.layers.0.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "36603dfdb3115686179fa1480cebe5d33c34c05c41c220897730397fbf2ff8ad.npy",
      "sha256": "5c3ebb765862bb30d5a97649edc449695aa9f351c35930c0388de688f9a81a61",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.1.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "64386ccb9663fdc1056904816333029acc284e188b294d32f0790ce92cc630fd.npy",
      "sha256": "1d5ba346708afb07e038c27d2f7bb3843e33e896ca4ad91e1a0e24629a7965ab",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.10.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "1ecc423a6d329aab7bd9f008a2a9afcf5a54423e20167eeb3c70491a3a83aa67.npy",
      "sha256": "deb562ca73d4bb0d8337fa70217179cccc2bcd33f8048e3f1f64047bcd04447b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.11.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "54a41f94f75423aa89a398bbaf59a702a41b47b3b4231f242591e1ef78b9fa87.npy",
      "sha256": "d08f7c41a38390b267526b5343aa56be85e51658235f08624ec7e66e51c1e9fd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.12.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0e5a902a6b36715df7b33bc20beb3f047f743c1f188dbfb7b97819905c65456c.npy",
      "sha256": "12c45f50d13ca2754f0ab3820c494c91af7f4f1244ca07247a82b332edc8b9fd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.13.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0c8eb283bbabad1e3f9d3953227c163d7a8fb0d0ed046f4e911ac7d4a6161335.npy",
      "sha256": "6e1cb3394886dbe5553a448f8155ca6a2adba2e3fc3c1198dcc57f8a562b6f63",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.14.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "d2544ee68d66946d23d977827c24cbae5d1c76907dc2a0d7ff3f45993606ff37.npy",
      "sha256": "bde503c029ea6c3d91167a14c7e351b66629f350157be8df97a23322be608cc3",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.15.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "017366cbb50180df94356b01c53217d02aaec84f8b0056b58fd3d777dbb895a5.npy",
      "sha256": "e5a12865962f742d8e259241cca9e17c96f366c0af13c31bae8faf00c1590cfe",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.16.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9ea551be1b29a5eeb9e87f5601d7cfc7bb5ccb6cac29c44b5998874c4b73b2c7.npy",
      "sha256": "b1cd52147d343a6da9ecb5bd672641f98943b88e64d3617fcdcc07f5bec41e9c",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.17.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c7d7331485a2d5a52e2415034ac56a0c44e89ccf7a20a5b41a769181147ffdba.npy",
      "sha256": "ff66fb334d072cee054fe7ffe7808a2fedfd05e94eb91100ff183bd09d3c8fdc",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.18.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "53b569f6a8c75e8ca7c16bcd6cd489da5812822c17b7376eb953ed71ebc98aa6.npy",
      "sha256": "0de7740437d0b6a930a0bcb2a17706eae6150de967864ffafbb64123762b9885",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.19.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "cfcb958acbc47f6a0c6ba6514bf424d4ebf1e65e05e99e266ce55601422aaa0d.npy",
      "sha256": "b4c4eb664b7d0cb8fc6019b319a43f1ef98c9b0a08e76015acef906c15ef96ae",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.2.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "587b2f04fcc0f785eabd10eb17224986b77cbb36a05b1748336421bd7ade3eb6.npy",
      "sha256": "ad631338250bb1422c14b17ce0a3935b90e9c75f3154afd94709074478a39aed",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.20.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "2d383293b38ed94a9ebe762db87adf6905c88e830ea656633fbb49c557cc77d6.npy",
      "sha256": "4543dcc704099263f435fb7d1999c994e9c34dacc944a716a17c478c413ceb8d",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.21.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "3438a2fc73755d660a160c20895b0a6da0495946cae579b995cd40f5e928a9dc.npy",
      "sha256": "62c2dde8fd0254152b95db5d88e7f848435f21f8d23fad80c43c16c84ae11a04",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.22.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6c141e33c8c72c1b73364682db8aafa901bf1243285958c5635cb193a6c2ae36.npy",
      "sha256": "0559287dc5e587667a235afa23b81ed7b4f9013fc1fa2568a5c9d0f8ae854b40",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.23.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "5c78ddbde110190e8894318b7ee805830f8c18f013b9719c1345f374eacf6619.npy",
      "sha256": "19d7397abdea9256f415fd66014d4a872c864ccf3ed3cc10417ce92c537d2fd4",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.24.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c10dfd8cd667bb3bd11a5498b78eb91c2fd8f12613f58840e08fb8f4c4909225.npy",
      "sha256": "4cbe086531307a8e22d5a6a068aaa27e3093079ac8cef6bd72296b94fc664dd2",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.25.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "e05dbd6bba2dbab7c6d2620760999fa8da0a931f35c796cfa67a524c9dbfcdee.npy",
      "sha256": "f9ef296959a57feaef693acd1f5fbc85db81f0ca9a8ef2086665e730e34f05fe",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.26.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "40a5ee7cd050fe72a30c25fb41b56de49817317cc263cec58fa06ddf9c167121.npy",
      "sha256": "ede2b237c422cea20adcb43170791c57ee313eba3ff8038738b0533fed7141a9",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.27.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "028401687464b1bab68c7d373b1ea93a52c007ac6bd4287350c5eaedfba24a15.npy",
      "sha256": "4d5e2fbcac0ec5136892530f753df7630b5df32373595416fce3a9d43d59093a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.28.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "ab27eb30016539a68bb7eefb5755e1a465539623088957d81cef532e70d6585c.npy",
      "sha256": "2af4852bc5f490825cdb8f57868b2d965e521971f51535fd662369420501e03a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.29.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "92a51fb78008338a6e9fb678a3bb8c335638b8d2af579768c7de69727f2e73b2.npy",
      "sha256": "76bbc0aceb953e4b8557ccdbd3fdf01cd34b65e9930a73b7ec0ad055e9b44600",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.3.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9b2ab0a8a58a33dbff4f2a3f8233aee784c022e419c49f47c60c1a5a19b10956.npy",
      "sha256": "816fb0086eb871c37564a7499e90684b93c8785daf0a242a6124bfa654cd00bd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.30.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "7ce8e6b4d02a88437cccee08eab258f37f317e3d2c9a24f121a907023d968a9f.npy",
      "sha256": "6bb39c14958857b4f7de37213cbd0daefdda69f74c994e684a1def6c21798b45",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.31.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "b452f40dd015b959083b8d22bca3356ee21a2ae3c337b5fd7ff3e6e2a15f4075.npy",
      "sha256": "bd04f2ac2b5c26e7694b3e46eb7d7ed062ce7eb6bbfbbe17b2b166d3f2446d5a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.32.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "a7960de319a2f44ee8eec19f96b4120fa232f77225f0bbcd2b0d93e5ce0b8ee6.npy",
      "sha256": "43300da96f53441c660b8064d01d4f07299ecf5c5954e5b772654e0ba9b6905c",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.33.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "89f1ede52230de17d6b49ef96369a32deb9514fe02a6b8a9625b08d803772ea4.npy",
      "sha256": "831ebcf256b0ae7c08c7550282f00e6e6114b597e4ea27b9184dca132b7371fc",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.34.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "8e450a9a8b75dd1a7da1b4e5f20aea8f2dbed0c7090d465f02ea612c1075a754.npy",
      "sha256": "f3aa754039bd0a38523cf3ad2e55c2d53c98a653ef76f981faa926859706271c",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.35.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "e0c8debc9a22af04c951ecc4ef9a332bb74f2d5cd30e3efb23ebe3c14a5a7bb1.npy",
      "sha256": "213f3f839132b94c953c6b866882ffa6fa5c7adfa913b2ee0d44f16ae61bd21c",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.4.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6987ba0209900f0d7dd1b10d752c445df903c37ff75df135ce0359c74d53fc43.npy",
      "sha256": "ff7239255fb333d01f9100e76f92c249d427eda27c057cb4b1f0ba2847511188",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.5.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "dec98df81839b4b65ccdd7c9df95408ae892f5815474a8d7c67baf0b9f07f1de.npy",
      "sha256": "83164f3d403735387fa092d3de2a62bc3ce4fdc0deea1beed7d51ca90a4fe54d",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.6.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "425f769cfe5c429de7106c2abadd4bfb1d28394b7498c51b1d7c3c4e13f58efc.npy",
      "sha256": "dfa17fa0449b75579b095286cec677e008d7a114e7f7c4399e05bf44c3915e3a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.7.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "71e4fb0843fbc0768d997eff6b0639877fcb5debca2170786911c707417cc736.npy",
      "sha256": "115b05b0ef0fc3a781c1c4033d2144be49564fe4fdb17132ea53a129d07cd860",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.8.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "fffa9c79d3df0b320e27ad7c77c394ed232d9aecde5f2c5f3c99828a44ce9c4f.npy",
      "sha256": "5d8b8be1417550b3101d7c140c67fdc23efcd198a67dc27d9d4597e6065a1394",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.9.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6cbc9dca72ae27d53869c0850b601f3f38f420b44106c3827c8e82423fcd0a4d.npy",
      "sha256": "199874d6c60f762cdafce3625c1ed55e2f1d67145bcd62e391a5ba172f4b596c",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f1d3a21809dec3af007a0e3e8d18370751190e3498db47c84c5378f698f8f05d",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6831896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 45,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 44,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.5,
    "repair_score": 0.5172413793103449,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第2轮

**当时目的与操作理由（原文）**

Round 2: replace round-1 scaling with 0.90 times W0 query-normalization weights in all 36 decoder layers. Opposite-direction test of broader attention and object coverage, motivated by round-1 downward count shifts and protected total regressions. No label fitting.

**本轮原记录的主分数**：`0.4482758620689655`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T1:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 4608,
  "id": "c-a46d6e61a1419d055d5d580238f9181b37c9bf90a904234c3e3f2b9b48d2bfe1",
  "l2": 11.861587432190387,
  "parent": "c-f1d3a21809dec3af007a0e3e8d18370751190e3498db47c84c5378f698f8f05d",
  "rationale": "Round 2: replace round-1 scaling with 0.90 times W0 query-normalization weights in all 36 decoder layers. Opposite-direction test of broader attention and object coverage, motivated by round-1 downward count shifts and protected total regressions. No label fitting.",
  "tensors": {
    "model.language_model.layers.0.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "36603dfdb3115686179fa1480cebe5d33c34c05c41c220897730397fbf2ff8ad.npy",
      "sha256": "2939c1292fd4c8271bec2d47f83d33ed5a15afa64576655d4cd645af8d6b6e60",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.1.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "64386ccb9663fdc1056904816333029acc284e188b294d32f0790ce92cc630fd.npy",
      "sha256": "518d8906b767c110a6a6bc4dbe6cea604770bf31eefad1613c8b1704dd65c102",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.10.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "1ecc423a6d329aab7bd9f008a2a9afcf5a54423e20167eeb3c70491a3a83aa67.npy",
      "sha256": "784c00e043ea8242aee0b188c6615b9fe8905be6b2c93374aa5ad53e2f6e1261",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.11.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "54a41f94f75423aa89a398bbaf59a702a41b47b3b4231f242591e1ef78b9fa87.npy",
      "sha256": "249b726e430ee2adc4e647ccb5ab56d381eba8685c818bd2f4b35865fd0544ff",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.12.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0e5a902a6b36715df7b33bc20beb3f047f743c1f188dbfb7b97819905c65456c.npy",
      "sha256": "c71004681cb5f83f4016d6b983ff3d33318029a9c3b0d3ab23db3de9bd8cb866",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.13.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0c8eb283bbabad1e3f9d3953227c163d7a8fb0d0ed046f4e911ac7d4a6161335.npy",
      "sha256": "e01ca0e69072dd20c20927381278f165fd626bfade83e10d30c4ffe1353de43b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.14.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "d2544ee68d66946d23d977827c24cbae5d1c76907dc2a0d7ff3f45993606ff37.npy",
      "sha256": "2c2c3212ae0d79d1d65afaca05c4116c3f2821f94069b850c22ca8de544baa50",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.15.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "017366cbb50180df94356b01c53217d02aaec84f8b0056b58fd3d777dbb895a5.npy",
      "sha256": "12e8a8cc5aab1a205c243c4d85c770bad34f01147b5c079376d720cf2c908d2f",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.16.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9ea551be1b29a5eeb9e87f5601d7cfc7bb5ccb6cac29c44b5998874c4b73b2c7.npy",
      "sha256": "e00da6d21c1b2316e463356744835f9cd635fca9f61694ed6cc5cb4a67b4960d",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.17.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c7d7331485a2d5a52e2415034ac56a0c44e89ccf7a20a5b41a769181147ffdba.npy",
      "sha256": "2af157a4d7b05b6ef8e19efc01cdcd901add3af3a8ff902cd7f9a3e58cfd3127",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.18.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "53b569f6a8c75e8ca7c16bcd6cd489da5812822c17b7376eb953ed71ebc98aa6.npy",
      "sha256": "808753bc18768ce8b34efb6c53c22cab9436e45b83d9c3fda5d1c045f2365696",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.19.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "cfcb958acbc47f6a0c6ba6514bf424d4ebf1e65e05e99e266ce55601422aaa0d.npy",
      "sha256": "e9972c083df159116ac92dd680eddc6cc20d507cb55fdf375bae5b5b29a74c87",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.2.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "587b2f04fcc0f785eabd10eb17224986b77cbb36a05b1748336421bd7ade3eb6.npy",
      "sha256": "62cec2a7cb5bf4b8eba730f16aece42f5aefb7f41c0bc79f3d7d569bbb77f3ec",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.20.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "2d383293b38ed94a9ebe762db87adf6905c88e830ea656633fbb49c557cc77d6.npy",
      "sha256": "64a371e38e0dabe5b27801e72ab29eef8126a44d21be5e94c1414bd35d277181",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.21.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "3438a2fc73755d660a160c20895b0a6da0495946cae579b995cd40f5e928a9dc.npy",
      "sha256": "1797b5fd0032a4be9322a35111f4a3b874b5c94c8336893a3e01976c62707155",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.22.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6c141e33c8c72c1b73364682db8aafa901bf1243285958c5635cb193a6c2ae36.npy",
      "sha256": "a45177c81a01b8badbb3a8a68c6979d52bf404b05b9a40f4281d2b392bbb468b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.23.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "5c78ddbde110190e8894318b7ee805830f8c18f013b9719c1345f374eacf6619.npy",
      "sha256": "7efc99e2e8f0241ba05bfd2ceafdef3e8be61c16256f6b616245daa70fd81ae1",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.24.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c10dfd8cd667bb3bd11a5498b78eb91c2fd8f12613f58840e08fb8f4c4909225.npy",
      "sha256": "d278e1142e9900c366ef3c45a28859415689e16b48d72cb0f2bee20347e9748e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.25.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "e05dbd6bba2dbab7c6d2620760999fa8da0a931f35c796cfa67a524c9dbfcdee.npy",
      "sha256": "ec379ad5775d7dc0b4c93902ab751ec989fd089c998f08aa1a3af450aa0f8f45",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.26.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "40a5ee7cd050fe72a30c25fb41b56de49817317cc263cec58fa06ddf9c167121.npy",
      "sha256": "05e4ecdc694d9dbad4410b433a22060d8d38a26566e9d029d57a49254b2a27b6",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.27.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "028401687464b1bab68c7d373b1ea93a52c007ac6bd4287350c5eaedfba24a15.npy",
      "sha256": "bd0ed3bb3e79d9550cf10280e743058958d81b8c8a6370f3952bdb6cd3185d6e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.28.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "ab27eb30016539a68bb7eefb5755e1a465539623088957d81cef532e70d6585c.npy",
      "sha256": "e4318d7a81321a0ee0caa1db2ea28853f50751c1f59919ca0b5a3a8f508c5a30",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.29.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "92a51fb78008338a6e9fb678a3bb8c335638b8d2af579768c7de69727f2e73b2.npy",
      "sha256": "f3c2fcfb55a2f529f2006e0652524a28f826ca6ae148a35e3455e5e71dd226fc",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.3.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9b2ab0a8a58a33dbff4f2a3f8233aee784c022e419c49f47c60c1a5a19b10956.npy",
      "sha256": "1638c88fbf76e932e80a887ba555d6a1067cc6e3241ae7b5afce512a04217d31",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.30.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "7ce8e6b4d02a88437cccee08eab258f37f317e3d2c9a24f121a907023d968a9f.npy",
      "sha256": "95de84dae2f941214e7f884e476960e0a441179ee75215b0ca74ef30157b32ec",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.31.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "b452f40dd015b959083b8d22bca3356ee21a2ae3c337b5fd7ff3e6e2a15f4075.npy",
      "sha256": "bebc556f2320be19b3f034a00f23a42cf09727faa5438101c5fa7e336f612f3f",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.32.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "a7960de319a2f44ee8eec19f96b4120fa232f77225f0bbcd2b0d93e5ce0b8ee6.npy",
      "sha256": "b276c7904a58a1c1719e2d7138e7e70bb8e44ea5eef2b23cfff97ec5bb149d4e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.33.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "89f1ede52230de17d6b49ef96369a32deb9514fe02a6b8a9625b08d803772ea4.npy",
      "sha256": "8a2996ab12f317ac064355ed9363ab78cdb38d33ce2a375b5fa76fddebe9fe4b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.34.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "8e450a9a8b75dd1a7da1b4e5f20aea8f2dbed0c7090d465f02ea612c1075a754.npy",
      "sha256": "99fcc19fddb6f24150a84632d8a8cf63a707f17de194ab15210630b5c4da6218",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.35.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "e0c8debc9a22af04c951ecc4ef9a332bb74f2d5cd30e3efb23ebe3c14a5a7bb1.npy",
      "sha256": "d1caae3d09f6d3deb6818a5d5b65d55e39ca1dc086ad907c63e573fd400792f7",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.4.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6987ba0209900f0d7dd1b10d752c445df903c37ff75df135ce0359c74d53fc43.npy",
      "sha256": "002ede6b55d8e4e7e6c68ecbc6aac12241d23328efee1ac92af317e12b8854e2",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.5.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "dec98df81839b4b65ccdd7c9df95408ae892f5815474a8d7c67baf0b9f07f1de.npy",
      "sha256": "8748a4de19ab1f17377afe0e034b10b0dec2a20f3b214134d5022d6beeba3dab",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.6.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "425f769cfe5c429de7106c2abadd4bfb1d28394b7498c51b1d7c3c4e13f58efc.npy",
      "sha256": "76d27571c2a340fc688680054ae5fd3f9115289f089534e13d8351481c915e16",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.7.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "71e4fb0843fbc0768d997eff6b0639877fcb5debca2170786911c707417cc736.npy",
      "sha256": "dd9b15c817bb3100bc454e8b4e504a463cdfb3c792404a429d58df2b164c3149",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.8.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "fffa9c79d3df0b320e27ad7c77c394ed232d9aecde5f2c5f3c99828a44ce9c4f.npy",
      "sha256": "2019454d142bb33146c24c5694ee81df9d15ab487c40cb37649330e08bdc97fd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.9.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6cbc9dca72ae27d53869c0850b601f3f38f420b44106c3827c8e82423fcd0a4d.npy",
      "sha256": "8fd23c90d2909a4fd35fb076eced89abd3e592fcd6bcd517a956bab95a6ab0ed",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-a46d6e61a1419d055d5d580238f9181b37c9bf90a904234c3e3f2b9b48d2bfe1",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6831896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 45,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 41,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 49,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.4482758620689655,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第3轮

**当时目的与操作理由（原文）**

Round 3: restore W0 outside decoder layers 0-11 and scale only their query-normalization weights by 1.10. Localization test following opposing global count shifts in rounds 1-2; seeks subset benefit without protected total losses. No label fitting.

**本轮原记录的主分数**：`0.49137931034482757`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-f68e10f9a84cf9fc2697e579abd7817050d25f358b6350e0cd6980af2fcdd10c",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.49137931034482757
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 1536,
  "id": "c-f68e10f9a84cf9fc2697e579abd7817050d25f358b6350e0cd6980af2fcdd10c",
  "l2": 6.681047700614516,
  "parent": "c-a46d6e61a1419d055d5d580238f9181b37c9bf90a904234c3e3f2b9b48d2bfe1",
  "rationale": "Round 3: restore W0 outside decoder layers 0-11 and scale only their query-normalization weights by 1.10. Localization test following opposing global count shifts in rounds 1-2; seeks subset benefit without protected total losses. No label fitting.",
  "tensors": {
    "model.language_model.layers.0.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "36603dfdb3115686179fa1480cebe5d33c34c05c41c220897730397fbf2ff8ad.npy",
      "sha256": "5c3ebb765862bb30d5a97649edc449695aa9f351c35930c0388de688f9a81a61",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.1.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "64386ccb9663fdc1056904816333029acc284e188b294d32f0790ce92cc630fd.npy",
      "sha256": "1d5ba346708afb07e038c27d2f7bb3843e33e896ca4ad91e1a0e24629a7965ab",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.10.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "1ecc423a6d329aab7bd9f008a2a9afcf5a54423e20167eeb3c70491a3a83aa67.npy",
      "sha256": "deb562ca73d4bb0d8337fa70217179cccc2bcd33f8048e3f1f64047bcd04447b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.11.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "54a41f94f75423aa89a398bbaf59a702a41b47b3b4231f242591e1ef78b9fa87.npy",
      "sha256": "d08f7c41a38390b267526b5343aa56be85e51658235f08624ec7e66e51c1e9fd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.2.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "587b2f04fcc0f785eabd10eb17224986b77cbb36a05b1748336421bd7ade3eb6.npy",
      "sha256": "ad631338250bb1422c14b17ce0a3935b90e9c75f3154afd94709074478a39aed",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.3.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9b2ab0a8a58a33dbff4f2a3f8233aee784c022e419c49f47c60c1a5a19b10956.npy",
      "sha256": "816fb0086eb871c37564a7499e90684b93c8785daf0a242a6124bfa654cd00bd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.4.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6987ba0209900f0d7dd1b10d752c445df903c37ff75df135ce0359c74d53fc43.npy",
      "sha256": "ff7239255fb333d01f9100e76f92c249d427eda27c057cb4b1f0ba2847511188",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.5.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "dec98df81839b4b65ccdd7c9df95408ae892f5815474a8d7c67baf0b9f07f1de.npy",
      "sha256": "83164f3d403735387fa092d3de2a62bc3ce4fdc0deea1beed7d51ca90a4fe54d",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.6.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "425f769cfe5c429de7106c2abadd4bfb1d28394b7498c51b1d7c3c4e13f58efc.npy",
      "sha256": "dfa17fa0449b75579b095286cec677e008d7a114e7f7c4399e05bf44c3915e3a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.7.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "71e4fb0843fbc0768d997eff6b0639877fcb5debca2170786911c707417cc736.npy",
      "sha256": "115b05b0ef0fc3a781c1c4033d2144be49564fe4fdb17132ea53a129d07cd860",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.8.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "fffa9c79d3df0b320e27ad7c77c394ed232d9aecde5f2c5f3c99828a44ce9c4f.npy",
      "sha256": "5d8b8be1417550b3101d7c140c67fdc23efcd198a67dc27d9d4597e6065a1394",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.9.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6cbc9dca72ae27d53869c0850b601f3f38f420b44106c3827c8e82423fcd0a4d.npy",
      "sha256": "199874d6c60f762cdafce3625c1ed55e2f1d67145bcd62e391a5ba172f4b596c",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f68e10f9a84cf9fc2697e579abd7817050d25f358b6350e0cd6980af2fcdd10c",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7004310344827587,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 30,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.49137931034482757,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第4轮

**当时目的与操作理由（原文）**

Round 4: restore all other tensors to W0 and scale decoder q_norm weights in layers 12-23 by 1.10. Matched-size middle-third localization comparison against the qualifying early-third round 3; no label fitting.

**本轮原记录的主分数**：`0.5086206896551724`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B1:T1:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 1536,
  "id": "c-0d281dbc3c7de8b7f1af7fd7646ee1374762be5dcd4ddff054134c92cd059034",
  "l2": 6.935081319021202,
  "parent": "c-f68e10f9a84cf9fc2697e579abd7817050d25f358b6350e0cd6980af2fcdd10c",
  "rationale": "Round 4: restore all other tensors to W0 and scale decoder q_norm weights in layers 12-23 by 1.10. Matched-size middle-third localization comparison against the qualifying early-third round 3; no label fitting.",
  "tensors": {
    "model.language_model.layers.12.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0e5a902a6b36715df7b33bc20beb3f047f743c1f188dbfb7b97819905c65456c.npy",
      "sha256": "12c45f50d13ca2754f0ab3820c494c91af7f4f1244ca07247a82b332edc8b9fd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.13.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0c8eb283bbabad1e3f9d3953227c163d7a8fb0d0ed046f4e911ac7d4a6161335.npy",
      "sha256": "6e1cb3394886dbe5553a448f8155ca6a2adba2e3fc3c1198dcc57f8a562b6f63",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.14.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "d2544ee68d66946d23d977827c24cbae5d1c76907dc2a0d7ff3f45993606ff37.npy",
      "sha256": "bde503c029ea6c3d91167a14c7e351b66629f350157be8df97a23322be608cc3",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.15.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "017366cbb50180df94356b01c53217d02aaec84f8b0056b58fd3d777dbb895a5.npy",
      "sha256": "e5a12865962f742d8e259241cca9e17c96f366c0af13c31bae8faf00c1590cfe",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.16.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9ea551be1b29a5eeb9e87f5601d7cfc7bb5ccb6cac29c44b5998874c4b73b2c7.npy",
      "sha256": "b1cd52147d343a6da9ecb5bd672641f98943b88e64d3617fcdcc07f5bec41e9c",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.17.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c7d7331485a2d5a52e2415034ac56a0c44e89ccf7a20a5b41a769181147ffdba.npy",
      "sha256": "ff66fb334d072cee054fe7ffe7808a2fedfd05e94eb91100ff183bd09d3c8fdc",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.18.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "53b569f6a8c75e8ca7c16bcd6cd489da5812822c17b7376eb953ed71ebc98aa6.npy",
      "sha256": "0de7740437d0b6a930a0bcb2a17706eae6150de967864ffafbb64123762b9885",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.19.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "cfcb958acbc47f6a0c6ba6514bf424d4ebf1e65e05e99e266ce55601422aaa0d.npy",
      "sha256": "b4c4eb664b7d0cb8fc6019b319a43f1ef98c9b0a08e76015acef906c15ef96ae",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.20.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "2d383293b38ed94a9ebe762db87adf6905c88e830ea656633fbb49c557cc77d6.npy",
      "sha256": "4543dcc704099263f435fb7d1999c994e9c34dacc944a716a17c478c413ceb8d",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.21.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "3438a2fc73755d660a160c20895b0a6da0495946cae579b995cd40f5e928a9dc.npy",
      "sha256": "62c2dde8fd0254152b95db5d88e7f848435f21f8d23fad80c43c16c84ae11a04",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.22.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6c141e33c8c72c1b73364682db8aafa901bf1243285958c5635cb193a6c2ae36.npy",
      "sha256": "0559287dc5e587667a235afa23b81ed7b4f9013fc1fa2568a5c9d0f8ae854b40",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.23.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "5c78ddbde110190e8894318b7ee805830f8c18f013b9719c1345f374eacf6619.npy",
      "sha256": "19d7397abdea9256f415fd66014d4a872c864ccf3ed3cc10417ce92c537d2fd4",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-0d281dbc3c7de8b7f1af7fd7646ee1374762be5dcd4ddff054134c92cd059034",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6853448275862069,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 45,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 45,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.5086206896551724,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第5轮

**当时目的与操作理由（原文）**

Round 5: W0-based 1.10 query-normalization scaling only in decoder layers 24-35. Completes matched-size early/middle/late localization of the attention-concentration effect, with no label fitting or accumulated prior edits.

**本轮原记录的主分数**：`0.4827586206896552`；保留原始0–1尺度。

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
  "changed_scalars": 1536,
  "id": "c-ff8f78787ad88c8f9b1cd2bb7b0f7c0f8bc51212ea89c3de2a5a88803b731b13",
  "l2": 6.928640825407036,
  "parent": "c-0d281dbc3c7de8b7f1af7fd7646ee1374762be5dcd4ddff054134c92cd059034",
  "rationale": "Round 5: W0-based 1.10 query-normalization scaling only in decoder layers 24-35. Completes matched-size early/middle/late localization of the attention-concentration effect, with no label fitting or accumulated prior edits.",
  "tensors": {
    "model.language_model.layers.24.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c10dfd8cd667bb3bd11a5498b78eb91c2fd8f12613f58840e08fb8f4c4909225.npy",
      "sha256": "4cbe086531307a8e22d5a6a068aaa27e3093079ac8cef6bd72296b94fc664dd2",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.25.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "e05dbd6bba2dbab7c6d2620760999fa8da0a931f35c796cfa67a524c9dbfcdee.npy",
      "sha256": "f9ef296959a57feaef693acd1f5fbc85db81f0ca9a8ef2086665e730e34f05fe",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.26.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "40a5ee7cd050fe72a30c25fb41b56de49817317cc263cec58fa06ddf9c167121.npy",
      "sha256": "ede2b237c422cea20adcb43170791c57ee313eba3ff8038738b0533fed7141a9",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.27.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "028401687464b1bab68c7d373b1ea93a52c007ac6bd4287350c5eaedfba24a15.npy",
      "sha256": "4d5e2fbcac0ec5136892530f753df7630b5df32373595416fce3a9d43d59093a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.28.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "ab27eb30016539a68bb7eefb5755e1a465539623088957d81cef532e70d6585c.npy",
      "sha256": "2af4852bc5f490825cdb8f57868b2d965e521971f51535fd662369420501e03a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.29.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "92a51fb78008338a6e9fb678a3bb8c335638b8d2af579768c7de69727f2e73b2.npy",
      "sha256": "76bbc0aceb953e4b8557ccdbd3fdf01cd34b65e9930a73b7ec0ad055e9b44600",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.30.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "7ce8e6b4d02a88437cccee08eab258f37f317e3d2c9a24f121a907023d968a9f.npy",
      "sha256": "6bb39c14958857b4f7de37213cbd0daefdda69f74c994e684a1def6c21798b45",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.31.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "b452f40dd015b959083b8d22bca3356ee21a2ae3c337b5fd7ff3e6e2a15f4075.npy",
      "sha256": "bd04f2ac2b5c26e7694b3e46eb7d7ed062ce7eb6bbfbbe17b2b166d3f2446d5a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.32.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "a7960de319a2f44ee8eec19f96b4120fa232f77225f0bbcd2b0d93e5ce0b8ee6.npy",
      "sha256": "43300da96f53441c660b8064d01d4f07299ecf5c5954e5b772654e0ba9b6905c",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.33.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "89f1ede52230de17d6b49ef96369a32deb9514fe02a6b8a9625b08d803772ea4.npy",
      "sha256": "831ebcf256b0ae7c08c7550282f00e6e6114b597e4ea27b9184dca132b7371fc",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.34.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "8e450a9a8b75dd1a7da1b4e5f20aea8f2dbed0c7090d465f02ea612c1075a754.npy",
      "sha256": "f3aa754039bd0a38523cf3ad2e55c2d53c98a653ef76f981faa926859706271c",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.35.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "e0c8debc9a22af04c951ecc4ef9a332bb74f2d5cd30e3efb23ebe3c14a5a7bb1.npy",
      "sha256": "213f3f839132b94c953c6b866882ffa6fa5c7adfa913b2ee0d44f16ae61bd21c",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-ff8f78787ad88c8f9b1cd2bb7b0f7c0f8bc51212ea89c3de2a5a88803b731b13",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6961206896551724,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.4827586206896552,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第6轮

**当时目的与操作理由（原文）**

Round 6: W0-based 0.90 query-normalization scaling only in decoder layers 0-11. Opposite-direction matched-location test of early object coverage, motivated by global broadening repairs of high-count groups and middle-third sharpening regressions. No label fitting.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 1536,
  "id": "c-126ff951062621de62e9682fdcd10a298ca213f75431f2ac25db3da24de390c1",
  "l2": 6.681630025230689,
  "parent": "c-ff8f78787ad88c8f9b1cd2bb7b0f7c0f8bc51212ea89c3de2a5a88803b731b13",
  "rationale": "Round 6: W0-based 0.90 query-normalization scaling only in decoder layers 0-11. Opposite-direction matched-location test of early object coverage, motivated by global broadening repairs of high-count groups and middle-third sharpening regressions. No label fitting.",
  "tensors": {
    "model.language_model.layers.0.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "36603dfdb3115686179fa1480cebe5d33c34c05c41c220897730397fbf2ff8ad.npy",
      "sha256": "2939c1292fd4c8271bec2d47f83d33ed5a15afa64576655d4cd645af8d6b6e60",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.1.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "64386ccb9663fdc1056904816333029acc284e188b294d32f0790ce92cc630fd.npy",
      "sha256": "518d8906b767c110a6a6bc4dbe6cea604770bf31eefad1613c8b1704dd65c102",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.10.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "1ecc423a6d329aab7bd9f008a2a9afcf5a54423e20167eeb3c70491a3a83aa67.npy",
      "sha256": "784c00e043ea8242aee0b188c6615b9fe8905be6b2c93374aa5ad53e2f6e1261",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.11.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "54a41f94f75423aa89a398bbaf59a702a41b47b3b4231f242591e1ef78b9fa87.npy",
      "sha256": "249b726e430ee2adc4e647ccb5ab56d381eba8685c818bd2f4b35865fd0544ff",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.2.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "587b2f04fcc0f785eabd10eb17224986b77cbb36a05b1748336421bd7ade3eb6.npy",
      "sha256": "62cec2a7cb5bf4b8eba730f16aece42f5aefb7f41c0bc79f3d7d569bbb77f3ec",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.3.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9b2ab0a8a58a33dbff4f2a3f8233aee784c022e419c49f47c60c1a5a19b10956.npy",
      "sha256": "1638c88fbf76e932e80a887ba555d6a1067cc6e3241ae7b5afce512a04217d31",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.4.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6987ba0209900f0d7dd1b10d752c445df903c37ff75df135ce0359c74d53fc43.npy",
      "sha256": "002ede6b55d8e4e7e6c68ecbc6aac12241d23328efee1ac92af317e12b8854e2",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.5.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "dec98df81839b4b65ccdd7c9df95408ae892f5815474a8d7c67baf0b9f07f1de.npy",
      "sha256": "8748a4de19ab1f17377afe0e034b10b0dec2a20f3b214134d5022d6beeba3dab",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.6.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "425f769cfe5c429de7106c2abadd4bfb1d28394b7498c51b1d7c3c4e13f58efc.npy",
      "sha256": "76d27571c2a340fc688680054ae5fd3f9115289f089534e13d8351481c915e16",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.7.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "71e4fb0843fbc0768d997eff6b0639877fcb5debca2170786911c707417cc736.npy",
      "sha256": "dd9b15c817bb3100bc454e8b4e504a463cdfb3c792404a429d58df2b164c3149",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.8.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "fffa9c79d3df0b320e27ad7c77c394ed232d9aecde5f2c5f3c99828a44ce9c4f.npy",
      "sha256": "2019454d142bb33146c24c5694ee81df9d15ab487c40cb37649330e08bdc97fd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.9.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6cbc9dca72ae27d53869c0850b601f3f38f420b44106c3827c8e82423fcd0a4d.npy",
      "sha256": "8fd23c90d2909a4fd35fb076eced89abd3e592fcd6bcd517a956bab95a6ab0ed",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-126ff951062621de62e9682fdcd10a298ca213f75431f2ac25db3da24de390c1",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6961206896551724,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第7轮

**当时目的与操作理由（原文）**

Round 7: W0-based q_norm scaling by 0.90 only in decoder layers 12-23. Tests whether middle-layer concentration drives the global broadening recoveries and total-count tradeoff. Early broadening was safe but gave no ordinary joint-score gain. No label fitting.

**本轮原记录的主分数**：`0.45689655172413796`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B0:T1:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 1536,
  "id": "c-f18f6c0c15ed7a96f07e8d140f470f32d82ecab4100dd821669ce4d3a3bbb091",
  "l2": 6.934385618951549,
  "parent": "c-126ff951062621de62e9682fdcd10a298ca213f75431f2ac25db3da24de390c1",
  "rationale": "Round 7: W0-based q_norm scaling by 0.90 only in decoder layers 12-23. Tests whether middle-layer concentration drives the global broadening recoveries and total-count tradeoff. Early broadening was safe but gave no ordinary joint-score gain. No label fitting.",
  "tensors": {
    "model.language_model.layers.12.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0e5a902a6b36715df7b33bc20beb3f047f743c1f188dbfb7b97819905c65456c.npy",
      "sha256": "c71004681cb5f83f4016d6b983ff3d33318029a9c3b0d3ab23db3de9bd8cb866",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.13.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0c8eb283bbabad1e3f9d3953227c163d7a8fb0d0ed046f4e911ac7d4a6161335.npy",
      "sha256": "e01ca0e69072dd20c20927381278f165fd626bfade83e10d30c4ffe1353de43b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.14.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "d2544ee68d66946d23d977827c24cbae5d1c76907dc2a0d7ff3f45993606ff37.npy",
      "sha256": "2c2c3212ae0d79d1d65afaca05c4116c3f2821f94069b850c22ca8de544baa50",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.15.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "017366cbb50180df94356b01c53217d02aaec84f8b0056b58fd3d777dbb895a5.npy",
      "sha256": "12e8a8cc5aab1a205c243c4d85c770bad34f01147b5c079376d720cf2c908d2f",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.16.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9ea551be1b29a5eeb9e87f5601d7cfc7bb5ccb6cac29c44b5998874c4b73b2c7.npy",
      "sha256": "e00da6d21c1b2316e463356744835f9cd635fca9f61694ed6cc5cb4a67b4960d",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.17.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c7d7331485a2d5a52e2415034ac56a0c44e89ccf7a20a5b41a769181147ffdba.npy",
      "sha256": "2af157a4d7b05b6ef8e19efc01cdcd901add3af3a8ff902cd7f9a3e58cfd3127",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.18.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "53b569f6a8c75e8ca7c16bcd6cd489da5812822c17b7376eb953ed71ebc98aa6.npy",
      "sha256": "808753bc18768ce8b34efb6c53c22cab9436e45b83d9c3fda5d1c045f2365696",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.19.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "cfcb958acbc47f6a0c6ba6514bf424d4ebf1e65e05e99e266ce55601422aaa0d.npy",
      "sha256": "e9972c083df159116ac92dd680eddc6cc20d507cb55fdf375bae5b5b29a74c87",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.20.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "2d383293b38ed94a9ebe762db87adf6905c88e830ea656633fbb49c557cc77d6.npy",
      "sha256": "64a371e38e0dabe5b27801e72ab29eef8126a44d21be5e94c1414bd35d277181",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.21.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "3438a2fc73755d660a160c20895b0a6da0495946cae579b995cd40f5e928a9dc.npy",
      "sha256": "1797b5fd0032a4be9322a35111f4a3b874b5c94c8336893a3e01976c62707155",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.22.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6c141e33c8c72c1b73364682db8aafa901bf1243285958c5635cb193a6c2ae36.npy",
      "sha256": "a45177c81a01b8badbb3a8a68c6979d52bf404b05b9a40f4281d2b392bbb468b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.23.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "5c78ddbde110190e8894318b7ee805830f8c18f013b9719c1345f374eacf6619.npy",
      "sha256": "7efc99e2e8f0241ba05bfd2ceafdef3e8be61c16256f6b616245daa70fd81ae1",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f18f6c0c15ed7a96f07e8d140f470f32d82ecab4100dd821669ce4d3a3bbb091",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6875,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 44,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4482758620689655,
    "repair_score": 0.45689655172413796,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第8轮

**当时目的与操作理由（原文）**

Round 8: W0-based q_norm scaling by 0.90 only in decoder layers 24-35. Completes opposite-direction localization; tests a later-stage alternative to middle broadening, which repaired high-count groups but violated total protection. No label fitting.

**本轮原记录的主分数**：`0.46551724137931033`；保留原始0–1尺度。

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
  "changed_scalars": 1536,
  "id": "c-042adbbb333a57b4e0926874681a25c5443998f29c922a59096bf7be333250c0",
  "l2": 6.925848157815086,
  "parent": "c-f18f6c0c15ed7a96f07e8d140f470f32d82ecab4100dd821669ce4d3a3bbb091",
  "rationale": "Round 8: W0-based q_norm scaling by 0.90 only in decoder layers 24-35. Completes opposite-direction localization; tests a later-stage alternative to middle broadening, which repaired high-count groups but violated total protection. No label fitting.",
  "tensors": {
    "model.language_model.layers.24.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c10dfd8cd667bb3bd11a5498b78eb91c2fd8f12613f58840e08fb8f4c4909225.npy",
      "sha256": "d278e1142e9900c366ef3c45a28859415689e16b48d72cb0f2bee20347e9748e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.25.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "e05dbd6bba2dbab7c6d2620760999fa8da0a931f35c796cfa67a524c9dbfcdee.npy",
      "sha256": "ec379ad5775d7dc0b4c93902ab751ec989fd089c998f08aa1a3af450aa0f8f45",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.26.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "40a5ee7cd050fe72a30c25fb41b56de49817317cc263cec58fa06ddf9c167121.npy",
      "sha256": "05e4ecdc694d9dbad4410b433a22060d8d38a26566e9d029d57a49254b2a27b6",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.27.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "028401687464b1bab68c7d373b1ea93a52c007ac6bd4287350c5eaedfba24a15.npy",
      "sha256": "bd0ed3bb3e79d9550cf10280e743058958d81b8c8a6370f3952bdb6cd3185d6e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.28.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "ab27eb30016539a68bb7eefb5755e1a465539623088957d81cef532e70d6585c.npy",
      "sha256": "e4318d7a81321a0ee0caa1db2ea28853f50751c1f59919ca0b5a3a8f508c5a30",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.29.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "92a51fb78008338a6e9fb678a3bb8c335638b8d2af579768c7de69727f2e73b2.npy",
      "sha256": "f3c2fcfb55a2f529f2006e0652524a28f826ca6ae148a35e3455e5e71dd226fc",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.30.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "7ce8e6b4d02a88437cccee08eab258f37f317e3d2c9a24f121a907023d968a9f.npy",
      "sha256": "95de84dae2f941214e7f884e476960e0a441179ee75215b0ca74ef30157b32ec",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.31.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "b452f40dd015b959083b8d22bca3356ee21a2ae3c337b5fd7ff3e6e2a15f4075.npy",
      "sha256": "bebc556f2320be19b3f034a00f23a42cf09727faa5438101c5fa7e336f612f3f",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.32.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "a7960de319a2f44ee8eec19f96b4120fa232f77225f0bbcd2b0d93e5ce0b8ee6.npy",
      "sha256": "b276c7904a58a1c1719e2d7138e7e70bb8e44ea5eef2b23cfff97ec5bb149d4e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.33.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "89f1ede52230de17d6b49ef96369a32deb9514fe02a6b8a9625b08d803772ea4.npy",
      "sha256": "8a2996ab12f317ac064355ed9363ab78cdb38d33ce2a375b5fa76fddebe9fe4b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.34.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "8e450a9a8b75dd1a7da1b4e5f20aea8f2dbed0c7090d465f02ea612c1075a754.npy",
      "sha256": "99fcc19fddb6f24150a84632d8a8cf63a707f17de194ab15210630b5c4da6218",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.35.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "e0c8debc9a22af04c951ecc4ef9a332bb74f2d5cd30e3efb23ebe3c14a5a7bb1.npy",
      "sha256": "d1caae3d09f6d3deb6818a5d5b65d55e39ca1dc086ad907c63e573fd400792f7",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-042adbbb333a57b4e0926874681a25c5443998f29c922a59096bf7be333250c0",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6918103448275862,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.46551724137931033,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第9轮

**当时目的与操作理由（原文）**

Round 9: restore decoder parameters to W0; multiply main visual merger LayerNorm weight and bias by 1.10. Verified patch-axis shapes first. Tests increased normalized visual input to the primary merger MLP for missed-instance counts; auxiliary mergers untouched. No label fitting.

**本轮原记录的主分数**：`0.46551724137931033`；保留原始0–1尺度。

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
  "changed_scalars": 2048,
  "id": "c-a9f1ac306fb9e1d186215b8e37c86a855a70a31e6d57dc7963b007b4e8e45fe6",
  "l2": 4.387127739035481,
  "parent": "c-042adbbb333a57b4e0926874681a25c5443998f29c922a59096bf7be333250c0",
  "rationale": "Round 9: restore decoder parameters to W0; multiply main visual merger LayerNorm weight and bias by 1.10. Verified patch-axis shapes first. Tests increased normalized visual input to the primary merger MLP for missed-instance counts; auxiliary mergers untouched. No label fitting.",
  "tensors": {
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "1784cbb08131301492f16c12e981799ee3b1f2d1b39f5b3de108989a9a7a5959",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "b9c0dfb962936b138ebb12fc30dd829e7e6f03477b3370b47b691653a6582aba",
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
  "candidate": "c-a9f1ac306fb9e1d186215b8e37c86a855a70a31e6d57dc7963b007b4e8e45fe6",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6939655172413793,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.46551724137931033,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第10轮

**当时目的与操作理由（原文）**

Round 10: main visual merger LayerNorm weight and bias at 0.90 times W0, all other parameters restored. Opposite-direction test of primary-versus-auxiliary visual feature balance after amplification failed to improve ordinary paired correctness. No label fitting.

**本轮原记录的主分数**：`0.4827586206896552`；保留原始0–1尺度。

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
  "changed_scalars": 2048,
  "id": "c-a5ed31b19143f9137343d24dc798da387702e0d3f063d9064f606cfbe9835d00",
  "l2": 4.387248738322701,
  "parent": "c-a9f1ac306fb9e1d186215b8e37c86a855a70a31e6d57dc7963b007b4e8e45fe6",
  "rationale": "Round 10: main visual merger LayerNorm weight and bias at 0.90 times W0, all other parameters restored. Opposite-direction test of primary-versus-auxiliary visual feature balance after amplification failed to improve ordinary paired correctness. No label fitting.",
  "tensors": {
    "model.visual.merger.norm.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1119e957850e55f2d054a76dbc1008db12033980c9a17db33de23eee9396530c.npy",
      "sha256": "b1b0f4a970291cc6344477ef0b98943a3634ba106ba50e8a951a17bc14a7fdb1",
      "shape": [
        1024
      ]
    },
    "model.visual.merger.norm.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "6d6cc04efbec6755cd2ae90b05ffe6d5f21f8aa3b97e3d947b80f35ca5bac196.npy",
      "sha256": "368e110652ee6c5c1eb72d5d51b2f8a19c6b5948755a5e38bdd9333fe88668b3",
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
  "candidate": "c-a5ed31b19143f9137343d24dc798da387702e0d3f063d9064f606cfbe9835d00",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6939655172413793,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.4827586206896552,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第11轮

**当时目的与操作理由（原文）**

Round 11: restore main merger to W0 and scale only auxiliary visual merger 0 LayerNorm weight and bias by 1.25. Tests increased intermediate visual-feature input, distinct from primary-path gain and decoder attention scaling. No label fitting.

**本轮原记录的主分数**：`0.46551724137931033`；保留原始0–1尺度。

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
  "changed_scalars": 8192,
  "id": "c-677f5e9c0b1e164e34e37243b30a798698ee350147e86148f9b361216a3ce2e5",
  "l2": 16.189284776030682,
  "parent": "c-a5ed31b19143f9137343d24dc798da387702e0d3f063d9064f606cfbe9835d00",
  "rationale": "Round 11: restore main merger to W0 and scale only auxiliary visual merger 0 LayerNorm weight and bias by 1.25. Tests increased intermediate visual-feature input, distinct from primary-path gain and decoder attention scaling. No label fitting.",
  "tensors": {
    "model.visual.deepstack_merger_list.0.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "9be04788b1c0d5b8af8b3e6837d5a8169494428b54f79b5890b670fb280ae24b.npy",
      "sha256": "c3bf3b3e7450f3176103999cf992cf3570dbec62078983e6472766db37a95768",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "4405e67c685b2c72daee37b6d354c0e802f6568d9356cb5c817eb07ca06c5f85",
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
  "candidate": "c-677f5e9c0b1e164e34e37243b30a798698ee350147e86148f9b361216a3ce2e5",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6961206896551724,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 30,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4482758620689655,
    "repair_score": 0.46551724137931033,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第12轮

**当时目的与操作理由（原文）**

Round 12: W0-based 1.25 scaling of auxiliary visual merger 1 LayerNorm weight and bias only. Matched-path comparison after merger-0 amplification affected mostly already-sensitive cells. Tests whether another intermediate visual path provides useful counting evidence. No label fitting.

**本轮原记录的主分数**：`0.4827586206896552`；保留原始0–1尺度。

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
  "changed_scalars": 8192,
  "id": "c-e1ed6e5010cc0fd30592f5e6f8cd8b6bc25f7afa59f41d2200034b8a22af506f",
  "l2": 16.36978324851548,
  "parent": "c-677f5e9c0b1e164e34e37243b30a798698ee350147e86148f9b361216a3ce2e5",
  "rationale": "Round 12: W0-based 1.25 scaling of auxiliary visual merger 1 LayerNorm weight and bias only. Matched-path comparison after merger-0 amplification affected mostly already-sensitive cells. Tests whether another intermediate visual path provides useful counting evidence. No label fitting.",
  "tensors": {
    "model.visual.deepstack_merger_list.1.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "3e0efc4703a8e12dc9c849ce2a8293cc2d3fd4caf53c6920525d819416d02881.npy",
      "sha256": "d171682ca35c15ee8de7b2750fa5711ef46da614c4d241b7946d222b9c2e2fa2",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.1.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "560c532031860531bd2f415a47e04cc88d7d4140097b4be709d2db61f8124e34.npy",
      "sha256": "f09f8903009a6576e2d94c0680d75d39f3ddd28465bf24f7ce0bffb7f7eb4513",
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
  "candidate": "c-e1ed6e5010cc0fd30592f5e6f8cd8b6bc25f7afa59f41d2200034b8a22af506f",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7004310344827587,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.4827586206896552,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第13轮

**当时目的与操作理由（原文）**

Round 13: W0-based 1.25 scaling of auxiliary visual merger 2 LayerNorm weight and bias only. Completes matched amplification comparison across auxiliary paths; examines repair overlap after merger 1 achieved five repairs without correctness regressions. No label fitting.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 8192,
  "id": "c-5a80d21553942c55dd5ed40893f6b141a7aa7ec0e3dea3bb8b85eed96143fcdd",
  "l2": 16.251703991518756,
  "parent": "c-e1ed6e5010cc0fd30592f5e6f8cd8b6bc25f7afa59f41d2200034b8a22af506f",
  "rationale": "Round 13: W0-based 1.25 scaling of auxiliary visual merger 2 LayerNorm weight and bias only. Completes matched amplification comparison across auxiliary paths; examines repair overlap after merger 1 achieved five repairs without correctness regressions. No label fitting.",
  "tensors": {
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
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-5a80d21553942c55dd5ed40893f6b141a7aa7ec0e3dea3bb8b85eed96143fcdd",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6896551724137931,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第14轮

**当时目的与操作理由（原文）**

Round 14: W0-based 0.75 scaling of auxiliary visual merger 0 LayerNorm weight and bias only. Opposite-direction control to round 11 amplification, testing whether attenuating this intermediate visual path improves counting while preserving protected cells. All other parameters restored; no label fitting.

**本轮原记录的主分数**：`0.5`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-45039bf791dedf86e8a723789a36cd43dad1f837e4de4fbc630e1a73664a1b55",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.5
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 8192,
  "id": "c-45039bf791dedf86e8a723789a36cd43dad1f837e4de4fbc630e1a73664a1b55",
  "l2": 16.199980169330136,
  "parent": "c-5a80d21553942c55dd5ed40893f6b141a7aa7ec0e3dea3bb8b85eed96143fcdd",
  "rationale": "Round 14: W0-based 0.75 scaling of auxiliary visual merger 0 LayerNorm weight and bias only. Opposite-direction control to round 11 amplification, testing whether attenuating this intermediate visual path improves counting while preserving protected cells. All other parameters restored; no label fitting.",
  "tensors": {
    "model.visual.deepstack_merger_list.0.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "9be04788b1c0d5b8af8b3e6837d5a8169494428b54f79b5890b670fb280ae24b.npy",
      "sha256": "e449a8d4698207615aabde461b26e7b65c4ac5ac631fc6ed6eac9bf125a54770",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "fc430fe41a80cb67a85d7214e4f82e6ecee623b51e388f0ca0b89dd337ebfa58",
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
  "candidate": "c-45039bf791dedf86e8a723789a36cd43dad1f837e4de4fbc630e1a73664a1b55",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7025862068965517,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.5,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第15轮

**当时目的与操作理由（原文）**

Round 15: W0-based 0.75 scaling of auxiliary visual merger 1 LayerNorm weight and bias only. Matched-size location comparison with round 14 merger-0 attenuation, which improved ordinary joint correctness without aggregate protected-cell losses. Also contrasts with round 12 merger-1 amplification. All other parameters restored; no label fitting.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 8192,
  "id": "c-e2531477103b69087580c0c77e207524516383f7281110dae3d5ecce721f78e0",
  "l2": 16.380614150451084,
  "parent": "c-45039bf791dedf86e8a723789a36cd43dad1f837e4de4fbc630e1a73664a1b55",
  "rationale": "Round 15: W0-based 0.75 scaling of auxiliary visual merger 1 LayerNorm weight and bias only. Matched-size location comparison with round 14 merger-0 attenuation, which improved ordinary joint correctness without aggregate protected-cell losses. Also contrasts with round 12 merger-1 amplification. All other parameters restored; no label fitting.",
  "tensors": {
    "model.visual.deepstack_merger_list.1.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "3e0efc4703a8e12dc9c849ce2a8293cc2d3fd4caf53c6920525d819416d02881.npy",
      "sha256": "40a7e1231b477d427f606cb036b957c54d37cf6fd9e9a5c4bbbf17207772b68c",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.1.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "560c532031860531bd2f415a47e04cc88d7d4140097b4be709d2db61f8124e34.npy",
      "sha256": "776d7b1e382247453ec3ed0a2511fd437b01759d49419bac605048b2f36a8db9",
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
  "candidate": "c-e2531477103b69087580c0c77e207524516383f7281110dae3d5ecce721f78e0",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6918103448275862,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 45,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第16轮

**当时目的与操作理由（原文）**

Round 16: W0-based 0.75 scaling of auxiliary visual merger 2 LayerNorm weight and bias only. Completes matched attenuation tests across auxiliary paths and contrasts with round 13 amplification. Merger-0 attenuation improved ordinary joint correctness; merger-1 attenuation did not. All other parameters restored; no label fitting.

**本轮原记录的主分数**：`0.46551724137931033`；保留原始0–1尺度。

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
  "changed_scalars": 8192,
  "id": "c-8444391eecdfc04d227f6a2ad239c1547e783e321608255a6cca0bf1126996fe",
  "l2": 16.260843776266267,
  "parent": "c-e2531477103b69087580c0c77e207524516383f7281110dae3d5ecce721f78e0",
  "rationale": "Round 16: W0-based 0.75 scaling of auxiliary visual merger 2 LayerNorm weight and bias only. Completes matched attenuation tests across auxiliary paths and contrasts with round 13 amplification. Merger-0 attenuation improved ordinary joint correctness; merger-1 attenuation did not. All other parameters restored; no label fitting.",
  "tensors": {
    "model.visual.deepstack_merger_list.2.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "c799d4aee219e92955f591ad2c4d2c88b62e6457a9fe175185b0e7ebd46401f5.npy",
      "sha256": "8462487b0fb6b5212317ce52a078c9c6ebc6417fa409a76bb8457307f805b0e1",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.2.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "89903596042f90ababf49242075a8bb755e9b3a6117537fd1a6d8f91fda37000.npy",
      "sha256": "54222208f835a8791edb9aa21efd41a623acad26b39561128a65c84e061731af",
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
  "candidate": "c-8444391eecdfc04d227f6a2ad239c1547e783e321608255a6cca0bf1126996fe",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6982758620689655,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.46551724137931033,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第17轮

**当时目的与操作理由（原文）**

Round 17: scale only auxiliary visual merger 0 LayerNorm weight by 0.75 from W0; its bias and all other parameters remain W0. Component ablation of the qualifying round 14 weight-and-bias attenuation, testing normalized-feature amplitude separately from the learned offset. No label fitting.

**本轮原记录的主分数**：`0.5`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-95b9144ef91655a0d0e74ee8dfcf4ab59153284d6972e7405bc67f57e320f9d1",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.5
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 4096,
  "id": "c-95b9144ef91655a0d0e74ee8dfcf4ab59153284d6972e7405bc67f57e320f9d1",
  "l2": 16.181859274511016,
  "parent": "c-8444391eecdfc04d227f6a2ad239c1547e783e321608255a6cca0bf1126996fe",
  "rationale": "Round 17: scale only auxiliary visual merger 0 LayerNorm weight by 0.75 from W0; its bias and all other parameters remain W0. Component ablation of the qualifying round 14 weight-and-bias attenuation, testing normalized-feature amplitude separately from the learned offset. No label fitting.",
  "tensors": {
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "fc430fe41a80cb67a85d7214e4f82e6ecee623b51e388f0ca0b89dd337ebfa58",
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
  "candidate": "c-95b9144ef91655a0d0e74ee8dfcf4ab59153284d6972e7405bc67f57e320f9d1",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7004310344827587,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.5,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第18轮

**当时目的与操作理由（原文）**

Round 18: scale only auxiliary visual merger 0 LayerNorm bias by 0.75 from W0; weight and all other parameters remain W0. Complementary component ablation to rounds 14 and 17, testing whether the learned-offset change alone contributes useful repairs or regressions. No label fitting.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 4096,
  "id": "c-8b9189ccde0f0b26fb616512b7cc1f6650448b5db4f1c3b48c38b867f0ab2c32",
  "l2": 0.7660208264868459,
  "parent": "c-95b9144ef91655a0d0e74ee8dfcf4ab59153284d6972e7405bc67f57e320f9d1",
  "rationale": "Round 18: scale only auxiliary visual merger 0 LayerNorm bias by 0.75 from W0; weight and all other parameters remain W0. Complementary component ablation to rounds 14 and 17, testing whether the learned-offset change alone contributes useful repairs or regressions. No label fitting.",
  "tensors": {
    "model.visual.deepstack_merger_list.0.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "9be04788b1c0d5b8af8b3e6837d5a8169494428b54f79b5890b670fb280ae24b.npy",
      "sha256": "e449a8d4698207615aabde461b26e7b65c4ac5ac631fc6ed6eac9bf125a54770",
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
  "candidate": "c-8b9189ccde0f0b26fb616512b7cc1f6650448b5db4f1c3b48c38b867f0ab2c32",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6918103448275862,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第19轮

**当时目的与操作理由（原文）**

Round 19: halve only auxiliary visual merger 0 linear_fc2.bias relative to W0. Tests attenuation of the constant output-feature offset, distinct from the successful normalization-weight change and the weak normalization-bias-only effect. Verified 2560 nonzero bias elements; all other parameters restored; no label fitting.

**本轮原记录的主分数**：`0.46551724137931033`；保留原始0–1尺度。

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
  "changed_scalars": 2560,
  "id": "c-7838b1f642d06cf319a6b863f55192d3cbae00da61c800a004f1447d46204c66",
  "l2": 0.25298389594386556,
  "parent": "c-8b9189ccde0f0b26fb616512b7cc1f6650448b5db4f1c3b48c38b867f0ab2c32",
  "rationale": "Round 19: halve only auxiliary visual merger 0 linear_fc2.bias relative to W0. Tests attenuation of the constant output-feature offset, distinct from the successful normalization-weight change and the weak normalization-bias-only effect. Verified 2560 nonzero bias elements; all other parameters restored; no label fitting.",
  "tensors": {
    "model.visual.deepstack_merger_list.0.linear_fc2.bias": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d7093aff514dea862f917d5ce40642bcf8e76048666a06927cc706e045848cdf.npy",
      "sha256": "979fcd288b61cf3af4662a65b503a232d3d684f61212f15148be51b0a27dd731",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-7838b1f642d06cf319a6b863f55192d3cbae00da61c800a004f1447d46204c66",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6896551724137931,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.46551724137931033,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第20轮

**当时目的与操作理由（原文）**

Round 20: scale only auxiliary visual merger 0 linear_fc2.bias by 1.5 from W0. Opposite-direction control to round 19 bias attenuation, which traded one repair for one regression and lowered ordinary joint correctness. Tests directional sensitivity of the constant output-feature offset. All other parameters restored; no label fitting.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 2560,
  "id": "c-3943cafc7f871d9f64907296ae657956d8eeb4639ef90ad36940b963b2d35cb4",
  "l2": 0.25287788522179255,
  "parent": "c-7838b1f642d06cf319a6b863f55192d3cbae00da61c800a004f1447d46204c66",
  "rationale": "Round 20: scale only auxiliary visual merger 0 linear_fc2.bias by 1.5 from W0. Opposite-direction control to round 19 bias attenuation, which traded one repair for one regression and lowered ordinary joint correctness. Tests directional sensitivity of the constant output-feature offset. All other parameters restored; no label fitting.",
  "tensors": {
    "model.visual.deepstack_merger_list.0.linear_fc2.bias": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d7093aff514dea862f917d5ce40642bcf8e76048666a06927cc706e045848cdf.npy",
      "sha256": "46fbaf0ec5b1b97bb20122c291ebe01740967cedbbe8c978eb351c96a2721623",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-3943cafc7f871d9f64907296ae657956d8eeb4639ef90ad36940b963b2d35cb4",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6918103448275862,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第21轮

**当时目的与操作理由（原文）**

Round 21: W0-based 1.10 scaling of decoder q_norm weights in layers 0-5 only. Spatially narrower component test of round 3's qualifying layers-0-11 patch, seeking retained repairs with fewer changed parameters and fewer regressions. Visual parameters and all other decoder parameters restored; no label fitting.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 768,
  "id": "c-b6489f666bb4311184ff2c3d7b3ff9b02418cfc5bbacae8869eee51091820d25",
  "l2": 4.6641946647878445,
  "parent": "c-3943cafc7f871d9f64907296ae657956d8eeb4639ef90ad36940b963b2d35cb4",
  "rationale": "Round 21: W0-based 1.10 scaling of decoder q_norm weights in layers 0-5 only. Spatially narrower component test of round 3's qualifying layers-0-11 patch, seeking retained repairs with fewer changed parameters and fewer regressions. Visual parameters and all other decoder parameters restored; no label fitting.",
  "tensors": {
    "model.language_model.layers.0.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "36603dfdb3115686179fa1480cebe5d33c34c05c41c220897730397fbf2ff8ad.npy",
      "sha256": "5c3ebb765862bb30d5a97649edc449695aa9f351c35930c0388de688f9a81a61",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.1.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "64386ccb9663fdc1056904816333029acc284e188b294d32f0790ce92cc630fd.npy",
      "sha256": "1d5ba346708afb07e038c27d2f7bb3843e33e896ca4ad91e1a0e24629a7965ab",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.2.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "587b2f04fcc0f785eabd10eb17224986b77cbb36a05b1748336421bd7ade3eb6.npy",
      "sha256": "ad631338250bb1422c14b17ce0a3935b90e9c75f3154afd94709074478a39aed",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.3.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9b2ab0a8a58a33dbff4f2a3f8233aee784c022e419c49f47c60c1a5a19b10956.npy",
      "sha256": "816fb0086eb871c37564a7499e90684b93c8785daf0a242a6124bfa654cd00bd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.4.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6987ba0209900f0d7dd1b10d752c445df903c37ff75df135ce0359c74d53fc43.npy",
      "sha256": "ff7239255fb333d01f9100e76f92c249d427eda27c057cb4b1f0ba2847511188",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.5.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "dec98df81839b4b65ccdd7c9df95408ae892f5815474a8d7c67baf0b9f07f1de.npy",
      "sha256": "83164f3d403735387fa092d3de2a62bc3ce4fdc0deea1beed7d51ca90a4fe54d",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-b6489f666bb4311184ff2c3d7b3ff9b02418cfc5bbacae8869eee51091820d25",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6918103448275862,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第22轮

**当时目的与操作理由（原文）**

Round 22: W0-based 1.10 scaling of decoder q_norm weights in layers 6-11 only. Complementary component test to round 21 layers 0-5 and round 3 layers 0-11. Tests whether the second half retains the broader early-layer joint-correctness benefit with fewer changed parameters. All other parameters restored to W0; no label fitting.

**本轮原记录的主分数**：`0.49137931034482757`；保留原始0–1尺度。

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
  "changed_scalars": 768,
  "id": "c-53c0bb8b0991478cd98e8f5ce332aa897d520fe536149f80ebbca2fe30366d47",
  "l2": 4.7834805849769175,
  "parent": "c-b6489f666bb4311184ff2c3d7b3ff9b02418cfc5bbacae8869eee51091820d25",
  "rationale": "Round 22: W0-based 1.10 scaling of decoder q_norm weights in layers 6-11 only. Complementary component test to round 21 layers 0-5 and round 3 layers 0-11. Tests whether the second half retains the broader early-layer joint-correctness benefit with fewer changed parameters. All other parameters restored to W0; no label fitting.",
  "tensors": {
    "model.language_model.layers.10.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "1ecc423a6d329aab7bd9f008a2a9afcf5a54423e20167eeb3c70491a3a83aa67.npy",
      "sha256": "deb562ca73d4bb0d8337fa70217179cccc2bcd33f8048e3f1f64047bcd04447b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.11.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "54a41f94f75423aa89a398bbaf59a702a41b47b3b4231f242591e1ef78b9fa87.npy",
      "sha256": "d08f7c41a38390b267526b5343aa56be85e51658235f08624ec7e66e51c1e9fd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.6.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "425f769cfe5c429de7106c2abadd4bfb1d28394b7498c51b1d7c3c4e13f58efc.npy",
      "sha256": "dfa17fa0449b75579b095286cec677e008d7a114e7f7c4399e05bf44c3915e3a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.7.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "71e4fb0843fbc0768d997eff6b0639877fcb5debca2170786911c707417cc736.npy",
      "sha256": "115b05b0ef0fc3a781c1c4033d2144be49564fe4fdb17132ea53a129d07cd860",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.8.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "fffa9c79d3df0b320e27ad7c77c394ed232d9aecde5f2c5f3c99828a44ce9c4f.npy",
      "sha256": "5d8b8be1417550b3101d7c140c67fdc23efcd198a67dc27d9d4597e6065a1394",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.9.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6cbc9dca72ae27d53869c0850b601f3f38f420b44106c3827c8e82423fcd0a4d.npy",
      "sha256": "199874d6c60f762cdafce3625c1ed55e2f1d67145bcd62e391a5ba172f4b596c",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-53c0bb8b0991478cd98e8f5ce332aa897d520fe536149f80ebbca2fe30366d47",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6982758620689655,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 30,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.49137931034482757,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第23轮

**当时目的与操作理由（原文）**

Round 23: W0-based 1.05 scaling of decoder q_norm weights in layers 12-23 only. Half-strength follow-up to round 4's 1.10 scaling, which improved ordinary joint correctness but violated a protected total-count cell. Tests whether reducing perturbation magnitude retains useful repairs while satisfying every protected-cell constraint. All other parameters restored to W0; uniform scaling without per-coordinate fitting.

**本轮原记录的主分数**：`0.5`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-4da8cb8f683f2f52fbe80fcdc29f947d26fbd20414b7cc7c00771583fa792995",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.5
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 1536,
  "id": "c-4da8cb8f683f2f52fbe80fcdc29f947d26fbd20414b7cc7c00771583fa792995",
  "l2": 3.4716712386025796,
  "parent": "c-53c0bb8b0991478cd98e8f5ce332aa897d520fe536149f80ebbca2fe30366d47",
  "rationale": "Round 23: W0-based 1.05 scaling of decoder q_norm weights in layers 12-23 only. Half-strength follow-up to round 4's 1.10 scaling, which improved ordinary joint correctness but violated a protected total-count cell. Tests whether reducing perturbation magnitude retains useful repairs while satisfying every protected-cell constraint. All other parameters restored to W0; uniform scaling without per-coordinate fitting.",
  "tensors": {
    "model.language_model.layers.12.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0e5a902a6b36715df7b33bc20beb3f047f743c1f188dbfb7b97819905c65456c.npy",
      "sha256": "8b2a29c9e98ea91de331eb8419f5fbc43c61fcbb3504431ae2a426d84f3b2d1b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.13.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0c8eb283bbabad1e3f9d3953227c163d7a8fb0d0ed046f4e911ac7d4a6161335.npy",
      "sha256": "3951b5219aceb6ffe5e2e1cf0989458d77a7fb8ce94366e856bbadd60ecad5f1",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.14.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "d2544ee68d66946d23d977827c24cbae5d1c76907dc2a0d7ff3f45993606ff37.npy",
      "sha256": "278714661feace44bfd0b63edf193a8e6966154f5d31f6c78947b5b50773d4dc",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.15.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "017366cbb50180df94356b01c53217d02aaec84f8b0056b58fd3d777dbb895a5.npy",
      "sha256": "9bee0ac3e200b8e241f8615630c5bf51c6d9913cc9d8d3e3b91e3e010d8ce2c0",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.16.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9ea551be1b29a5eeb9e87f5601d7cfc7bb5ccb6cac29c44b5998874c4b73b2c7.npy",
      "sha256": "482e5624c7c14581c3bae355f283fb45fdbd1cc869541d73b27224fd92905957",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.17.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c7d7331485a2d5a52e2415034ac56a0c44e89ccf7a20a5b41a769181147ffdba.npy",
      "sha256": "53123ee92fc1f5b9df83c60a2ea3a9ff59c40021c7bf81d7bf2fb5b3c257360e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.18.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "53b569f6a8c75e8ca7c16bcd6cd489da5812822c17b7376eb953ed71ebc98aa6.npy",
      "sha256": "40e6e549d580ae9b7d548cbd78fcf1d88befd1e4949a06da4466bccbce1d2c7e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.19.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "cfcb958acbc47f6a0c6ba6514bf424d4ebf1e65e05e99e266ce55601422aaa0d.npy",
      "sha256": "4efc1caa094bab8cb3d1f47d73dad75de56f63bf3f390a58306c26ea61ec3922",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.20.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "2d383293b38ed94a9ebe762db87adf6905c88e830ea656633fbb49c557cc77d6.npy",
      "sha256": "5850499910eaa8969a742f1c5981a71c7aa250ec620b8dca16f90f719e8ddddd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.21.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "3438a2fc73755d660a160c20895b0a6da0495946cae579b995cd40f5e928a9dc.npy",
      "sha256": "2ada132270d0909df1a158ed76d5352ea9f57001a252d429a9517318af1e9273",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.22.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6c141e33c8c72c1b73364682db8aafa901bf1243285958c5635cb193a6c2ae36.npy",
      "sha256": "7b3c865718d777457db139f3432221346fbb5f1e7ec110c2090d8495b3550f0f",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.23.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "5c78ddbde110190e8894318b7ee805830f8c18f013b9719c1345f374eacf6619.npy",
      "sha256": "f52e2fb6d4dd1651871ce9de52844afb0437255516ffeea42f47c677cfe3189f",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-4da8cb8f683f2f52fbe80fcdc29f947d26fbd20414b7cc7c00771583fa792995",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6918103448275862,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.5,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第24轮

**当时目的与操作理由（原文）**

Round 24: combine W0-based auxiliary visual merger 0 norm.weight scaling by 0.75 with decoder q_norm scaling by 1.05 in layers 12-23. Rounds 17 and 23 tie on ordinary joint correctness but have partly distinct repairs and markedly different regression profiles. Tests interaction rather than assuming additive benefits; all remaining parameters stay at W0. Uniform component scales, no per-coordinate fitting.

**本轮原记录的主分数**：`0.49137931034482757`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "not_selected": "Protection failed in wording/order/prompt cell: B1:T1:-:total"
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 5632,
  "id": "c-b258d2f36729228bbda08be2ed3bf95a7b47879bbdc025df583daa153f1b9611",
  "l2": 16.55007766655548,
  "parent": "c-4da8cb8f683f2f52fbe80fcdc29f947d26fbd20414b7cc7c00771583fa792995",
  "rationale": "Round 24: combine W0-based auxiliary visual merger 0 norm.weight scaling by 0.75 with decoder q_norm scaling by 1.05 in layers 12-23. Rounds 17 and 23 tie on ordinary joint correctness but have partly distinct repairs and markedly different regression profiles. Tests interaction rather than assuming additive benefits; all remaining parameters stay at W0. Uniform component scales, no per-coordinate fitting.",
  "tensors": {
    "model.language_model.layers.12.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0e5a902a6b36715df7b33bc20beb3f047f743c1f188dbfb7b97819905c65456c.npy",
      "sha256": "8b2a29c9e98ea91de331eb8419f5fbc43c61fcbb3504431ae2a426d84f3b2d1b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.13.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0c8eb283bbabad1e3f9d3953227c163d7a8fb0d0ed046f4e911ac7d4a6161335.npy",
      "sha256": "3951b5219aceb6ffe5e2e1cf0989458d77a7fb8ce94366e856bbadd60ecad5f1",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.14.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "d2544ee68d66946d23d977827c24cbae5d1c76907dc2a0d7ff3f45993606ff37.npy",
      "sha256": "278714661feace44bfd0b63edf193a8e6966154f5d31f6c78947b5b50773d4dc",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.15.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "017366cbb50180df94356b01c53217d02aaec84f8b0056b58fd3d777dbb895a5.npy",
      "sha256": "9bee0ac3e200b8e241f8615630c5bf51c6d9913cc9d8d3e3b91e3e010d8ce2c0",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.16.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9ea551be1b29a5eeb9e87f5601d7cfc7bb5ccb6cac29c44b5998874c4b73b2c7.npy",
      "sha256": "482e5624c7c14581c3bae355f283fb45fdbd1cc869541d73b27224fd92905957",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.17.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c7d7331485a2d5a52e2415034ac56a0c44e89ccf7a20a5b41a769181147ffdba.npy",
      "sha256": "53123ee92fc1f5b9df83c60a2ea3a9ff59c40021c7bf81d7bf2fb5b3c257360e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.18.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "53b569f6a8c75e8ca7c16bcd6cd489da5812822c17b7376eb953ed71ebc98aa6.npy",
      "sha256": "40e6e549d580ae9b7d548cbd78fcf1d88befd1e4949a06da4466bccbce1d2c7e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.19.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "cfcb958acbc47f6a0c6ba6514bf424d4ebf1e65e05e99e266ce55601422aaa0d.npy",
      "sha256": "4efc1caa094bab8cb3d1f47d73dad75de56f63bf3f390a58306c26ea61ec3922",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.20.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "2d383293b38ed94a9ebe762db87adf6905c88e830ea656633fbb49c557cc77d6.npy",
      "sha256": "5850499910eaa8969a742f1c5981a71c7aa250ec620b8dca16f90f719e8ddddd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.21.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "3438a2fc73755d660a160c20895b0a6da0495946cae579b995cd40f5e928a9dc.npy",
      "sha256": "2ada132270d0909df1a158ed76d5352ea9f57001a252d429a9517318af1e9273",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.22.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6c141e33c8c72c1b73364682db8aafa901bf1243285958c5635cb193a6c2ae36.npy",
      "sha256": "7b3c865718d777457db139f3432221346fbb5f1e7ec110c2090d8495b3550f0f",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.23.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "5c78ddbde110190e8894318b7ee805830f8c18f013b9719c1345f374eacf6619.npy",
      "sha256": "f52e2fb6d4dd1651871ce9de52844afb0437255516ffeea42f47c677cfe3189f",
      "shape": [
        128
      ]
    },
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "fc430fe41a80cb67a85d7214e4f82e6ecee623b51e388f0ca0b89dd337ebfa58",
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
  "candidate": "c-b258d2f36729228bbda08be2ed3bf95a7b47879bbdc025df583daa153f1b9611",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6831896551724138,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 45,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 45,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.49137931034482757,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第25轮

**当时目的与操作理由（原文）**

Round 25: combine W0-based auxiliary visual merger 0 norm.weight scaling by 0.75 with decoder q_norm scaling by 1.10 in layers 6-11. Component rounds 17 and 22 each satisfy protected-cell limits. Contrasts their early-decoder interaction with round 24's failing middle-decoder combination; benefits are not assumed additive. All other parameters restored to W0; no per-coordinate fitting.

**本轮原记录的主分数**：`0.49137931034482757`；保留原始0–1尺度。

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
  "changed_scalars": 4864,
  "id": "c-07d4ce651380447f5ef55340c12d8479ab01a8056f043c5af04d897232710587",
  "l2": 16.874070525126093,
  "parent": "c-b258d2f36729228bbda08be2ed3bf95a7b47879bbdc025df583daa153f1b9611",
  "rationale": "Round 25: combine W0-based auxiliary visual merger 0 norm.weight scaling by 0.75 with decoder q_norm scaling by 1.10 in layers 6-11. Component rounds 17 and 22 each satisfy protected-cell limits. Contrasts their early-decoder interaction with round 24's failing middle-decoder combination; benefits are not assumed additive. All other parameters restored to W0; no per-coordinate fitting.",
  "tensors": {
    "model.language_model.layers.10.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "1ecc423a6d329aab7bd9f008a2a9afcf5a54423e20167eeb3c70491a3a83aa67.npy",
      "sha256": "deb562ca73d4bb0d8337fa70217179cccc2bcd33f8048e3f1f64047bcd04447b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.11.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "54a41f94f75423aa89a398bbaf59a702a41b47b3b4231f242591e1ef78b9fa87.npy",
      "sha256": "d08f7c41a38390b267526b5343aa56be85e51658235f08624ec7e66e51c1e9fd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.6.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "425f769cfe5c429de7106c2abadd4bfb1d28394b7498c51b1d7c3c4e13f58efc.npy",
      "sha256": "dfa17fa0449b75579b095286cec677e008d7a114e7f7c4399e05bf44c3915e3a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.7.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "71e4fb0843fbc0768d997eff6b0639877fcb5debca2170786911c707417cc736.npy",
      "sha256": "115b05b0ef0fc3a781c1c4033d2144be49564fe4fdb17132ea53a129d07cd860",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.8.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "fffa9c79d3df0b320e27ad7c77c394ed232d9aecde5f2c5f3c99828a44ce9c4f.npy",
      "sha256": "5d8b8be1417550b3101d7c140c67fdc23efcd198a67dc27d9d4597e6065a1394",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.9.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6cbc9dca72ae27d53869c0850b601f3f38f420b44106c3827c8e82423fcd0a4d.npy",
      "sha256": "199874d6c60f762cdafce3625c1ed55e2f1d67145bcd62e391a5ba172f4b596c",
      "shape": [
        128
      ]
    },
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "fc430fe41a80cb67a85d7214e4f82e6ecee623b51e388f0ca0b89dd337ebfa58",
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
  "candidate": "c-07d4ce651380447f5ef55340c12d8479ab01a8056f043c5af04d897232710587",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6961206896551724,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 30,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.49137931034482757,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第26轮

**当时目的与操作理由（原文）**

Round 26: combine auxiliary visual merger 0 norm.weight at 0.75 times W0 with auxiliary merger 1 norm.weight and norm.bias at 1.25 times W0. Component rounds 17 and 12 each gave five repairs without correctness regressions, with partly different repaired examples. Tests cross-visual-path interaction after decoder/visual combinations failed to exceed the best joint score. Decoder and all other weights restored to W0; uniform scales only.

**本轮原记录的主分数**：`0.5`；保留原始0–1尺度。

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
  "changed_scalars": 12288,
  "id": "c-ab83cd7c812d8c01545f6ed48961141dfd3966fc9609f5ad0ca2e28264dc00b0",
  "l2": 23.01787073522345,
  "parent": "c-07d4ce651380447f5ef55340c12d8479ab01a8056f043c5af04d897232710587",
  "rationale": "Round 26: combine auxiliary visual merger 0 norm.weight at 0.75 times W0 with auxiliary merger 1 norm.weight and norm.bias at 1.25 times W0. Component rounds 17 and 12 each gave five repairs without correctness regressions, with partly different repaired examples. Tests cross-visual-path interaction after decoder/visual combinations failed to exceed the best joint score. Decoder and all other weights restored to W0; uniform scales only.",
  "tensors": {
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "fc430fe41a80cb67a85d7214e4f82e6ecee623b51e388f0ca0b89dd337ebfa58",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.1.norm.bias": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "3e0efc4703a8e12dc9c849ce2a8293cc2d3fd4caf53c6920525d819416d02881.npy",
      "sha256": "d171682ca35c15ee8de7b2750fa5711ef46da614c4d241b7946d222b9c2e2fa2",
      "shape": [
        4096
      ]
    },
    "model.visual.deepstack_merger_list.1.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "560c532031860531bd2f415a47e04cc88d7d4140097b4be709d2db61f8124e34.npy",
      "sha256": "f09f8903009a6576e2d94c0680d75d39f3ddd28465bf24f7ce0bffb7f7eb4513",
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
  "candidate": "c-ab83cd7c812d8c01545f6ed48961141dfd3966fc9609f5ad0ca2e28264dc00b0",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7047413793103449,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.5,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第27轮

**当时目的与操作理由（原文）**

Round 27: scale only auxiliary visual merger 0 norm.weight to 0.50 times W0. Dose-response test against round 17's 0.75 weight-only scaling, which gave five repairs without correctness regressions. Tests whether stronger normalized-feature attenuation extends the limited repair effect or introduces damage, without combination confounding. Bias and every other parameter restored to W0.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 4096,
  "id": "c-9ae2ee7086a81264af33a6ec94c1eb45d70dc17d3d8c65fb7f0fabd8c242ae0f",
  "l2": 32.36366727572281,
  "parent": "c-ab83cd7c812d8c01545f6ed48961141dfd3966fc9609f5ad0ca2e28264dc00b0",
  "rationale": "Round 27: scale only auxiliary visual merger 0 norm.weight to 0.50 times W0. Dose-response test against round 17's 0.75 weight-only scaling, which gave five repairs without correctness regressions. Tests whether stronger normalized-feature attenuation extends the limited repair effect or introduces damage, without combination confounding. Bias and every other parameter restored to W0.",
  "tensors": {
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "3860f8ee2c75bd59b57de2789b078e62a3155eb73e934b8f066a181d15677590",
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
  "candidate": "c-9ae2ee7086a81264af33a6ec94c1eb45d70dc17d3d8c65fb7f0fabd8c242ae0f",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6896551724137931,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第28轮

**当时目的与操作理由（原文）**

Round 28: scale only auxiliary visual merger 0 norm.weight to 0.875 times W0. Smaller-dose comparison with round 17's 0.75 and round 27's 0.50 scaling. The stronger dose traded six repairs for six regressions and lost the joint-score gain; this tests whether half the round-17 attenuation preserves useful repairs with lower perturbation magnitude. Bias and all other parameters restored to W0.

**本轮原记录的主分数**：`0.49137931034482757`；保留原始0–1尺度。

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
  "changed_scalars": 4096,
  "id": "c-5145020977553906706156a60fd449db62389da6bed96324ebf1bc1fcb6bfaf2",
  "l2": 8.090009730914362,
  "parent": "c-9ae2ee7086a81264af33a6ec94c1eb45d70dc17d3d8c65fb7f0fabd8c242ae0f",
  "rationale": "Round 28: scale only auxiliary visual merger 0 norm.weight to 0.875 times W0. Smaller-dose comparison with round 17's 0.75 and round 27's 0.50 scaling. The stronger dose traded six repairs for six regressions and lost the joint-score gain; this tests whether half the round-17 attenuation preserves useful repairs with lower perturbation magnitude. Bias and all other parameters restored to W0.",
  "tensors": {
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "05adaece39855547c6ba1daa53a805d63f0448ce44b1cb5d23090642190b6feb",
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
  "candidate": "c-5145020977553906706156a60fd449db62389da6bed96324ebf1bc1fcb6bfaf2",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7004310344827587,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.49137931034482757,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第29轮

**当时目的与操作理由（原文）**

Round 29: scale decoder q_norm weights in layers 12-17 only by 1.05 from W0. Component ablation of round 23's selected layers-12-23 patch, testing whether the first half retains its joint-correctness gain with fewer changed parameters and fewer regressions. All other parameters restored to W0; uniform scaling without per-coordinate fitting.

**本轮原记录的主分数**：`0.46551724137931033`；保留原始0–1尺度。

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
  "changed_scalars": 768,
  "id": "c-f491a2c7cd0869db4f9f3e2414f8c19fce285abee1c9f71bfdf3f0d16802a4d3",
  "l2": 2.412276875345274,
  "parent": "c-5145020977553906706156a60fd449db62389da6bed96324ebf1bc1fcb6bfaf2",
  "rationale": "Round 29: scale decoder q_norm weights in layers 12-17 only by 1.05 from W0. Component ablation of round 23's selected layers-12-23 patch, testing whether the first half retains its joint-correctness gain with fewer changed parameters and fewer regressions. All other parameters restored to W0; uniform scaling without per-coordinate fitting.",
  "tensors": {
    "model.language_model.layers.12.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0e5a902a6b36715df7b33bc20beb3f047f743c1f188dbfb7b97819905c65456c.npy",
      "sha256": "8b2a29c9e98ea91de331eb8419f5fbc43c61fcbb3504431ae2a426d84f3b2d1b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.13.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0c8eb283bbabad1e3f9d3953227c163d7a8fb0d0ed046f4e911ac7d4a6161335.npy",
      "sha256": "3951b5219aceb6ffe5e2e1cf0989458d77a7fb8ce94366e856bbadd60ecad5f1",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.14.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "d2544ee68d66946d23d977827c24cbae5d1c76907dc2a0d7ff3f45993606ff37.npy",
      "sha256": "278714661feace44bfd0b63edf193a8e6966154f5d31f6c78947b5b50773d4dc",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.15.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "017366cbb50180df94356b01c53217d02aaec84f8b0056b58fd3d777dbb895a5.npy",
      "sha256": "9bee0ac3e200b8e241f8615630c5bf51c6d9913cc9d8d3e3b91e3e010d8ce2c0",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.16.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9ea551be1b29a5eeb9e87f5601d7cfc7bb5ccb6cac29c44b5998874c4b73b2c7.npy",
      "sha256": "482e5624c7c14581c3bae355f283fb45fdbd1cc869541d73b27224fd92905957",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.17.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c7d7331485a2d5a52e2415034ac56a0c44e89ccf7a20a5b41a769181147ffdba.npy",
      "sha256": "53123ee92fc1f5b9df83c60a2ea3a9ff59c40021c7bf81d7bf2fb5b3c257360e",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f491a2c7cd0869db4f9f3e2414f8c19fce285abee1c9f71bfdf3f0d16802a4d3",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6853448275862069,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.46551724137931033,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第30轮

**当时目的与操作理由（原文）**

Round 30: scale decoder q_norm weights in layers 18-23 only by 1.05 from W0. Complementary component ablation to round 29's layers 12-17 and round 23's selected layers 12-23 patch. Tests whether the second half retains the broader joint-correctness gain with smaller support and fewer regressions. All remaining parameters restored to W0; uniform scaling without per-coordinate fitting. Final planned repair round.

**本轮原记录的主分数**：`0.49137931034482757`；保留原始0–1尺度。

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
  "changed_scalars": 768,
  "id": "c-705b997e6b0a6effe03f29252c3a44b247e652779619b245e2497e07e85357e4",
  "l2": 2.4966820914194923,
  "parent": "c-f491a2c7cd0869db4f9f3e2414f8c19fce285abee1c9f71bfdf3f0d16802a4d3",
  "rationale": "Round 30: scale decoder q_norm weights in layers 18-23 only by 1.05 from W0. Complementary component ablation to round 29's layers 12-17 and round 23's selected layers 12-23 patch. Tests whether the second half retains the broader joint-correctness gain with smaller support and fewer regressions. All remaining parameters restored to W0; uniform scaling without per-coordinate fitting. Final planned repair round.",
  "tensors": {
    "model.language_model.layers.18.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "53b569f6a8c75e8ca7c16bcd6cd489da5812822c17b7376eb953ed71ebc98aa6.npy",
      "sha256": "40e6e549d580ae9b7d548cbd78fcf1d88befd1e4949a06da4466bccbce1d2c7e",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.19.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "cfcb958acbc47f6a0c6ba6514bf424d4ebf1e65e05e99e266ce55601422aaa0d.npy",
      "sha256": "4efc1caa094bab8cb3d1f47d73dad75de56f63bf3f390a58306c26ea61ec3922",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.20.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "2d383293b38ed94a9ebe762db87adf6905c88e830ea656633fbb49c557cc77d6.npy",
      "sha256": "5850499910eaa8969a742f1c5981a71c7aa250ec620b8dca16f90f719e8ddddd",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.21.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "3438a2fc73755d660a160c20895b0a6da0495946cae579b995cd40f5e928a9dc.npy",
      "sha256": "2ada132270d0909df1a158ed76d5352ea9f57001a252d429a9517318af1e9273",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.22.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6c141e33c8c72c1b73364682db8aafa901bf1243285958c5635cb193a6c2ae36.npy",
      "sha256": "7b3c865718d777457db139f3432221346fbb5f1e7ec110c2090d8495b3550f0f",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.23.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "5c78ddbde110190e8894318b7ee805830f8c18f013b9719c1345f374eacf6619.npy",
      "sha256": "f52e2fb6d4dd1651871ce9de52844afb0437255516ffeea42f47c677cfe3189f",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-705b997e6b0a6effe03f29252c3a44b247e652779619b245e2497e07e85357e4",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6961206896551724,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.49137931034482757,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第31轮

**当时目的与操作理由（原文）**

Round 31 of 50: multiply decoder post_attention_layernorm.weight in layers 0-5 by 0.95 from W0. Tests reduced normalized input gain to the early gated MLP branches, distinct from prior query-normalization edits. This is not assumed to be uniform MLP-output scaling because the MLP is nonlinear. All other parameters restored to W0; no per-coordinate label fitting. Planned opposite-direction control at 1.05.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-119aff2a83cdc498e5f21b58d474bc9f671cc6ddcfc184abad5b07bb0c34d516",
  "l2": 4.1150956841167154,
  "parent": "c-705b997e6b0a6effe03f29252c3a44b247e652779619b245e2497e07e85357e4",
  "rationale": "Round 31 of 50: multiply decoder post_attention_layernorm.weight in layers 0-5 by 0.95 from W0. Tests reduced normalized input gain to the early gated MLP branches, distinct from prior query-normalization edits. This is not assumed to be uniform MLP-output scaling because the MLP is nonlinear. All other parameters restored to W0; no per-coordinate label fitting. Planned opposite-direction control at 1.05.",
  "tensors": {
    "model.language_model.layers.0.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "05ed179a84377b7dc3df9b1bf573f5c566c290127691c81c9a7c5712f5fcf112.npy",
      "sha256": "f433f50bee3c0d750f69df61ca31af07ce0f5ed00d7bdbe78b6013a59d61aa7f",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.1.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d1702dddc15006975683fb200437c43ee6f7d8eeef263760e245b03327c3a7b7.npy",
      "sha256": "2b69335c1f353fc8ce65e2efc6cd4a1cfccd8ffc9dca6c989b9096685a1a2ae0",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.2.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "1aa9a96bda9730a0ce3e3633f0fb6402bea8d464629e1fed0c7ede9935447313.npy",
      "sha256": "eb4a7cd1aec08bc3b35c90eb20e35195ce3af661f713832792e3a07f7057dd6b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.3.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d93b584db1da53cc27060b059e791ab63aa6541240cb8137dc674112633aa858.npy",
      "sha256": "2e003988b7f554717bee19a68e5889f4a1bbf7714f8f12d1298f8b02c2016cc4",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.4.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "023548598f0a61df3fa3ab5ac5c2e93edfdf9db5c6442994f5d260ff2708cb23.npy",
      "sha256": "84f21af9b3666da1ae2f1160ad739d9ad8ed3d68daa67fea3854c4c1bfe0b524",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.5.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "fca28f60b1f6e807e3256c0878577b0e69848c60ed16affeafbec27b5b6702ca.npy",
      "sha256": "a966cccb3748655cf78a59b8ee130595b0d21bf4e25e6f8754b130998f0c39c9",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-119aff2a83cdc498e5f21b58d474bc9f671cc6ddcfc184abad5b07bb0c34d516",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6939655172413793,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第32轮

**当时目的与操作理由（原文）**

Round 32 of 50: multiply decoder post_attention_layernorm.weight in layers 0-5 by 1.05 from W0. Opposite-direction control to round 31's 0.95 scaling, which repaired two B1 responses without improving ordinary joint correctness. Tests amplification of early gated-MLP inputs rather than query attention temperature. All other parameters restored to W0; uniform scaling only.

**本轮原记录的主分数**：`0.49137931034482757`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-fad3adc259e74535470bb04ed581f1e33357f27aced29d75cd4c0d159e3ae1c4",
  "l2": 4.108664246519217,
  "parent": "c-119aff2a83cdc498e5f21b58d474bc9f671cc6ddcfc184abad5b07bb0c34d516",
  "rationale": "Round 32 of 50: multiply decoder post_attention_layernorm.weight in layers 0-5 by 1.05 from W0. Opposite-direction control to round 31's 0.95 scaling, which repaired two B1 responses without improving ordinary joint correctness. Tests amplification of early gated-MLP inputs rather than query attention temperature. All other parameters restored to W0; uniform scaling only.",
  "tensors": {
    "model.language_model.layers.0.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "05ed179a84377b7dc3df9b1bf573f5c566c290127691c81c9a7c5712f5fcf112.npy",
      "sha256": "30a910811d48b4404d671c713c3e8674dec078e9445fc6c4d2488a2d4d9bf0f1",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.1.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d1702dddc15006975683fb200437c43ee6f7d8eeef263760e245b03327c3a7b7.npy",
      "sha256": "ee6b3a7d8ab8a481a2eb9b89ec55ab651de5a1fde75573f58dedcf3269bf362c",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.2.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "1aa9a96bda9730a0ce3e3633f0fb6402bea8d464629e1fed0c7ede9935447313.npy",
      "sha256": "685832e67c06d4f259150a819bd6376d8fc4c6830b638f86720d8e3cd3588e01",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.3.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d93b584db1da53cc27060b059e791ab63aa6541240cb8137dc674112633aa858.npy",
      "sha256": "f6795e282491651cb104fb3331fb61001a2938e65b3cb3a19efb3997486a5e90",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.4.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "023548598f0a61df3fa3ab5ac5c2e93edfdf9db5c6442994f5d260ff2708cb23.npy",
      "sha256": "d43ef11d659c4044c0bc4d3b4b5dc559c12527b91273db28a4f82c12898a1c5d",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.5.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "fca28f60b1f6e807e3256c0878577b0e69848c60ed16affeafbec27b5b6702ca.npy",
      "sha256": "49875f362cb295b0d791916f5c1055242ecff1abb25200c0794c306c7384965b",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-fad3adc259e74535470bb04ed581f1e33357f27aced29d75cd4c0d159e3ae1c4",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7025862068965517,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.49137931034482757,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第33轮

**当时目的与操作理由（原文）**

Round 33 of 50: scale decoder post_attention_layernorm.weight in layers 12-17 by 0.95 from W0. Depth comparison with round 31's layers 0-5 attenuation, using the same number of normalization coordinates. Tests middle-layer gated-MLP input gain independently of the query-normalization family. All other parameters restored to W0; no per-coordinate fitting.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-2f1aae095bbffb1cb230a287e3826e268b85be178a5a6b37c010d05721f063d7",
  "l2": 4.044637643362981,
  "parent": "c-fad3adc259e74535470bb04ed581f1e33357f27aced29d75cd4c0d159e3ae1c4",
  "rationale": "Round 33 of 50: scale decoder post_attention_layernorm.weight in layers 12-17 by 0.95 from W0. Depth comparison with round 31's layers 0-5 attenuation, using the same number of normalization coordinates. Tests middle-layer gated-MLP input gain independently of the query-normalization family. All other parameters restored to W0; no per-coordinate fitting.",
  "tensors": {
    "model.language_model.layers.12.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "38ab1af53594a322359ea38432b3dc750bcb91d4a2637db901eb612595afcb33.npy",
      "sha256": "8ebfcdbfe8b9bf0359c6e743bf8022ed22b5f3a52abbaedf23fa59c72f2ee0a6",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.13.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d20951e482434decfad222fc6d29ff564ae334de099a97193051ccdad0e14d02.npy",
      "sha256": "f32e09dbe7ba06793e14072b17f91e0c8bcbb218092caf0166ca1d604e5f2d9e",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.14.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "6baf5d9b9f232516da9f9b7972f3dbadbe72f087dc67372c0f607f219060a9db.npy",
      "sha256": "fb63c96423e3233bbd2204e517311cea80d8a5f1226f7eec857b666420249954",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.15.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bd6c9acf6cb3ceb63a9952a79e1c2a94d4939937d0291a72fc7486f16a4ac352.npy",
      "sha256": "2b0e0892258c84bdb519c5fc84ecd796de8389673a1c86539df93810e4151ebc",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.16.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "2ac41399d4aae1ee398ec64ff25446dd72c3655cf1382cde58cf1d1c5c543301.npy",
      "sha256": "9e560ae1b40ec8d429cc284bcbbc0393d44861a0dd343d455c1d41f6710bef73",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.17.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "47206503346692dab752e1caa599acc36a1615ea21f0443ccfc9ba0ed132df5e.npy",
      "sha256": "ae336b1cca5dbcbd7b53d310cd020ef746514840bd4d37c177d9bbfe49b1b20e",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-2f1aae095bbffb1cb230a287e3826e268b85be178a5a6b37c010d05721f063d7",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6896551724137931,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第34轮

**当时目的与操作理由（原文）**

Round 34 of 50: scale decoder post_attention_layernorm.weight in layers 12-17 by 1.05 from W0. Opposite-direction control to round 33, whose attenuation repaired a total/subset pair but introduced two correctness regressions and left ordinary joint correctness at baseline. Tests direction-specific middle-MLP input sensitivity. All other parameters restored to W0; uniform scaling only.

**本轮原记录的主分数**：`0.49137931034482757`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-1eabc82fff88b2bbd2c1e85958a3913260d4ff6b01863e5ca66c4071863d7f2e",
  "l2": 4.041826228637078,
  "parent": "c-2f1aae095bbffb1cb230a287e3826e268b85be178a5a6b37c010d05721f063d7",
  "rationale": "Round 34 of 50: scale decoder post_attention_layernorm.weight in layers 12-17 by 1.05 from W0. Opposite-direction control to round 33, whose attenuation repaired a total/subset pair but introduced two correctness regressions and left ordinary joint correctness at baseline. Tests direction-specific middle-MLP input sensitivity. All other parameters restored to W0; uniform scaling only.",
  "tensors": {
    "model.language_model.layers.12.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "38ab1af53594a322359ea38432b3dc750bcb91d4a2637db901eb612595afcb33.npy",
      "sha256": "a5113ec611b141707930b558ca1b15bbc289acc103e76cce7e474dcb92abda09",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.13.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d20951e482434decfad222fc6d29ff564ae334de099a97193051ccdad0e14d02.npy",
      "sha256": "09235692bf225512282aa9f70d7ddf5048a16d85c1766349ef0b7aaf9d2a0388",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.14.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "6baf5d9b9f232516da9f9b7972f3dbadbe72f087dc67372c0f607f219060a9db.npy",
      "sha256": "0cbf660704ff34277693c4d946542d2095727f9fe33749eedc753fabc73b5ee7",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.15.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "bd6c9acf6cb3ceb63a9952a79e1c2a94d4939937d0291a72fc7486f16a4ac352.npy",
      "sha256": "80b109c22e3f8425ab4df79a3139317cae2e7201d00d889b87bdcb6f23c47aa7",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.16.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "2ac41399d4aae1ee398ec64ff25446dd72c3655cf1382cde58cf1d1c5c543301.npy",
      "sha256": "cf7028355a4dfce527e1a7d159050e13256ecbfa353c606410b02072e66b476c",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.17.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "47206503346692dab752e1caa599acc36a1615ea21f0443ccfc9ba0ed132df5e.npy",
      "sha256": "34812833481987657b8fb7e59f3c875ec3326d7a78b23ba47a542f4ffd984d3d",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-1eabc82fff88b2bbd2c1e85958a3913260d4ff6b01863e5ca66c4071863d7f2e",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7047413793103449,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 49,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.49137931034482757,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第35轮

**当时目的与操作理由（原文）**

Round 35 of 50: scale decoder post_attention_layernorm.weight in layers 30-35 by 0.95 from W0. Tests late-layer gated-MLP input attenuation against the same-size early- and middle-layer interventions, without directly editing output-token weights. All other parameters restored to W0; uniform scaling only. Plan an opposite-direction control at 1.05.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-9f2761dea5d6beab3eb8fcf6124638047bd1ffe62f7ac1c3c5fdfb435f7b6bbc",
  "l2": 8.927043891643525,
  "parent": "c-1eabc82fff88b2bbd2c1e85958a3913260d4ff6b01863e5ca66c4071863d7f2e",
  "rationale": "Round 35 of 50: scale decoder post_attention_layernorm.weight in layers 30-35 by 0.95 from W0. Tests late-layer gated-MLP input attenuation against the same-size early- and middle-layer interventions, without directly editing output-token weights. All other parameters restored to W0; uniform scaling only. Plan an opposite-direction control at 1.05.",
  "tensors": {
    "model.language_model.layers.30.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "5c452cdadd844c0e20ca6c509710a21ac7ae7e51bd6175f52b7543770622e7b6.npy",
      "sha256": "9222a5cee69ce78247148c36da0ec2b97d2b21ab05378d088b9eb75d29a9b54a",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.31.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "e6754a6205d962cadaca0c8ed560cce35221f4cb84e41a25015da7f7c3ded049.npy",
      "sha256": "3ba1de0ea40688bb2c2b62e578d8ab66145b1b63249e6a7ecd1f1661937b009a",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.32.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "80cefa0544ae569149c4a07862576ca5da69e741cc207ec323ef44ad4d9dae90.npy",
      "sha256": "4d2760deda67b2a76c82d1e18762cf84695d085e5872281f4dd72fa53f84c7f4",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.33.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9b4af14a457db696af7978a37f9e92368846acee7bd2f4100e3d3a94b7118ea4.npy",
      "sha256": "8619f5ec0aef6f8eeff0f70ac9efa1b29b379503f3592bdecf3ab01b56823b11",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.34.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "543515350d491da202167c101deaa5b2a3208682ce355bd3a8bdb972b5db793e.npy",
      "sha256": "9d09613b04d8c7b18744481266bdc665da6e69f7feafcbc510d3f8ea0c55b3c6",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.35.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "a576574c49097aee0bef4791e361dba80b1da27c2bf2060a895999e227072b7e.npy",
      "sha256": "d6b144c9ec0e2efc67946f71719562fb71ec46e9d5c3b4fd247acdddda940ca7",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-9f2761dea5d6beab3eb8fcf6124638047bd1ffe62f7ac1c3c5fdfb435f7b6bbc",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6918103448275862,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第36轮

**当时目的与操作理由（原文）**

Round 36 of 50: scale decoder post_attention_layernorm.weight in layers 30-35 by 1.05 from W0. Opposite-direction control to round 35's 0.95 scaling, which left ordinary wording-averaged joint correctness at 55/116 with two repaired responses and one regression. Tests direction-specific late gated-MLP input sensitivity. All other parameters restored to W0; uniform scaling only.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-a59e247f5431f971a64f58d4147ce6f9e56eb03083ce4fe8bfa8a110d76abe28",
  "l2": 8.914935923632918,
  "parent": "c-9f2761dea5d6beab3eb8fcf6124638047bd1ffe62f7ac1c3c5fdfb435f7b6bbc",
  "rationale": "Round 36 of 50: scale decoder post_attention_layernorm.weight in layers 30-35 by 1.05 from W0. Opposite-direction control to round 35's 0.95 scaling, which left ordinary wording-averaged joint correctness at 55/116 with two repaired responses and one regression. Tests direction-specific late gated-MLP input sensitivity. All other parameters restored to W0; uniform scaling only.",
  "tensors": {
    "model.language_model.layers.30.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "5c452cdadd844c0e20ca6c509710a21ac7ae7e51bd6175f52b7543770622e7b6.npy",
      "sha256": "7ceb056afe5c84d1cc3b98ad9693e9b01f2fcd9a693b27dfbf5ad6b9c9273753",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.31.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "e6754a6205d962cadaca0c8ed560cce35221f4cb84e41a25015da7f7c3ded049.npy",
      "sha256": "a532568b3e221f3b116e9333af9671792e174bd0da163241480d9480c3283831",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.32.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "80cefa0544ae569149c4a07862576ca5da69e741cc207ec323ef44ad4d9dae90.npy",
      "sha256": "6435ef8d7c17220b967078d8d6f964b82bf862688096ecb4a8192ff5fa11ffba",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.33.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "9b4af14a457db696af7978a37f9e92368846acee7bd2f4100e3d3a94b7118ea4.npy",
      "sha256": "4915e608e141fec9801507ba81e2fd8dfc8603d95aa783f28d9e72782449870d",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.34.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "543515350d491da202167c101deaa5b2a3208682ce355bd3a8bdb972b5db793e.npy",
      "sha256": "fb86d3b5b4ac964eb4458eac75ccaa57002112dc1065229a5f8cd7c9cda8807f",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.35.post_attention_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "a576574c49097aee0bef4791e361dba80b1da27c2bf2060a895999e227072b7e.npy",
      "sha256": "6475328195b0d19f3d9e408c0edf47f4981945a52b59033fd8ea88c84cbbc42a",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-a59e247f5431f971a64f58d4147ce6f9e56eb03083ce4fe8bfa8a110d76abe28",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6896551724137931,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第37轮

**当时目的与操作理由（原文）**

Round 37 of 50: scale decoder input_layernorm.weight in layers 0-5 by 0.95 from W0. Tests early attention-branch input gain, distinct from post-attention MLP-input and q_norm interventions. Q/K normalization largely cancels uniform input amplitude in ideal arithmetic, whereas the value path remains amplitude-sensitive; numerical effects prevent assuming exact equivalence to output scaling. All other parameters restored to W0. Planned opposite-direction control at 1.05; uniform scaling only.

**本轮原记录的主分数**：`0.46551724137931033`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-e69160f8033dbb12d33d07b16de31547ff0d0d8901db007dcdcf61d09e24bd98",
  "l2": 0.5715935028165076,
  "parent": "c-a59e247f5431f971a64f58d4147ce6f9e56eb03083ce4fe8bfa8a110d76abe28",
  "rationale": "Round 37 of 50: scale decoder input_layernorm.weight in layers 0-5 by 0.95 from W0. Tests early attention-branch input gain, distinct from post-attention MLP-input and q_norm interventions. Q/K normalization largely cancels uniform input amplitude in ideal arithmetic, whereas the value path remains amplitude-sensitive; numerical effects prevent assuming exact equivalence to output scaling. All other parameters restored to W0. Planned opposite-direction control at 1.05; uniform scaling only.",
  "tensors": {
    "model.language_model.layers.0.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d18dd9237fbce1c611e0670d5dc757a1114e93f07606cee8784f5f40b4b52827.npy",
      "sha256": "ccd797137aa4fd459a6aef347be20479ff72e53240f8f26217ff4f50d2aab484",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.1.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "fd3e9aa3b5190792e2ae5feef960d00afc5193c99cec0c0db3f885e7aa72e2b7.npy",
      "sha256": "379dc65e95725d98fd9a55bc41b4ef0b71fc79048a8a203019be20784a779a9b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.2.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "2041d4454b8cb67836330a465afa84171c935b14d3f642335bfe5bdb1dfb6dca.npy",
      "sha256": "e947d0f507e6d13e93b8b14385a6f447d8126e793b636188f9946398b066db53",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.3.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "cd4dfb87bdab3a4debfa21083312ef29e3495826d2e18d81b5218a0663d423f7.npy",
      "sha256": "323da2b13a93a43ecd56f78abeb76913d745810d9c94a4e07f244a661cc9661d",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.4.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ff04d1b5ea28422154ae4f5b782bcde2feeae34288830517b710a0ca68f2e3aa.npy",
      "sha256": "d712a7d98088b67459222dcc71b326d463745d55d880fe1b6c0b747f1b228f1c",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.5.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "dcaee351d2e3be283dd14c3a6de58ba5936cd200433f1dd8306a5412ecb0defb.npy",
      "sha256": "d32d32af277045f1d27dcc540c7ee85368c041707b062d8dd2e2ff6e50cc048d",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-e69160f8033dbb12d33d07b16de31547ff0d0d8901db007dcdcf61d09e24bd98",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6918103448275862,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.46551724137931033,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第38轮

**当时目的与操作理由（原文）**

Round 38 of 50: scale decoder input_layernorm.weight in layers 0-5 by 1.05 from W0. Opposite-direction control to round 37's attenuation, which produced two repairs and one regression but reduced ordinary wording-averaged joint correctness from 55/116 to 54/116. Tests early attention-input amplification independently of MLP-input and query-normalization edits. All other parameters restored to W0; uniform scaling only.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-68d9cf5251a8c5cc907a705c890a7418c3b34e2e078d2cdb6856971fc04a9450",
  "l2": 0.5719508433798144,
  "parent": "c-e69160f8033dbb12d33d07b16de31547ff0d0d8901db007dcdcf61d09e24bd98",
  "rationale": "Round 38 of 50: scale decoder input_layernorm.weight in layers 0-5 by 1.05 from W0. Opposite-direction control to round 37's attenuation, which produced two repairs and one regression but reduced ordinary wording-averaged joint correctness from 55/116 to 54/116. Tests early attention-input amplification independently of MLP-input and query-normalization edits. All other parameters restored to W0; uniform scaling only.",
  "tensors": {
    "model.language_model.layers.0.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "d18dd9237fbce1c611e0670d5dc757a1114e93f07606cee8784f5f40b4b52827.npy",
      "sha256": "c55bcc61dc32d7d5449a38fe640a2b499672848d317df764e4af20804dd914c7",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.1.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "fd3e9aa3b5190792e2ae5feef960d00afc5193c99cec0c0db3f885e7aa72e2b7.npy",
      "sha256": "fbaf9fc05125c41485929df55b6db7d154ad56fd1e03e2e7ab9ca702ebdc93b4",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.2.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "2041d4454b8cb67836330a465afa84171c935b14d3f642335bfe5bdb1dfb6dca.npy",
      "sha256": "72eb34aa3cbb0ebd4b00cbc18288781244d7543ade921abc40a1d08d4f3fd8a4",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.3.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "cd4dfb87bdab3a4debfa21083312ef29e3495826d2e18d81b5218a0663d423f7.npy",
      "sha256": "a90bc6ba6a9af64db378126be5d96939444ae706e6e8b93685f7e740f912fa2d",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.4.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "ff04d1b5ea28422154ae4f5b782bcde2feeae34288830517b710a0ca68f2e3aa.npy",
      "sha256": "10db807da07f24c0beed693d7e637fb51629f764a2e4c4698c1a12815a139827",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.5.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "dcaee351d2e3be283dd14c3a6de58ba5936cd200433f1dd8306a5412ecb0defb.npy",
      "sha256": "f41a4ed46d20bde0d45ea454125f9456b9659d198fd3a36bcea6e4a49fe0d863",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-68d9cf5251a8c5cc907a705c890a7418c3b34e2e078d2cdb6856971fc04a9450",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6896551724137931,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第39轮

**当时目的与操作理由（原文）**

Round 39 of 50: scale decoder input_layernorm.weight in layers 12-17 by 0.95 from W0. Depth comparison with round 37's layers 0-5 attenuation, using the same number of normalization coordinates. Tests middle-layer attention-input gain independently of the previously tested middle-layer MLP-input and q_norm interventions. All other parameters restored to W0; uniform scaling only. Planned opposite-direction control at 1.05.

**本轮原记录的主分数**：`0.49137931034482757`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-33eebedccdeb74903e4c6900686def3c3b74ade655a09773d0491b31d56ff529",
  "l2": 2.893191790861521,
  "parent": "c-68d9cf5251a8c5cc907a705c890a7418c3b34e2e078d2cdb6856971fc04a9450",
  "rationale": "Round 39 of 50: scale decoder input_layernorm.weight in layers 12-17 by 0.95 from W0. Depth comparison with round 37's layers 0-5 attenuation, using the same number of normalization coordinates. Tests middle-layer attention-input gain independently of the previously tested middle-layer MLP-input and q_norm interventions. All other parameters restored to W0; uniform scaling only. Planned opposite-direction control at 1.05.",
  "tensors": {
    "model.language_model.layers.12.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "e57f2ba1dd92e4a12b6cb857f22dae6a82f8de0b8703535bc51543485e079b22.npy",
      "sha256": "27057907bfbb94cd8ca6330530862f9f41f78946c61fb0ad24f2cc6af86b5762",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.13.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "028ac9c30d8e1e9060986a456afde270a51d39a590ec017f0a8af6971f6a9539.npy",
      "sha256": "ab9a86629116f6d334ce884d200d3c464521f429416580d55664d2be161022da",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.14.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "81723cc2bda8566eca79b387adb6a32f9a1657b727b93cd3e6c1ec56cee125d7.npy",
      "sha256": "9e7d016c8d36f703dc34af34a737d2b3cc90e04a1a2bceefd506716398e237b0",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.15.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f5048c39ae1fe62ea97fcc03d65cf73c355d27080918af6be3bcd045d9053a43.npy",
      "sha256": "3e0deb29b1d9e74edd0d718a71b617390ae6bb0da887acd1776da1ab7406389b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.16.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b2561341cf7a992be6fe49fecf46a8e3be0de6e1d3009aab60a7b5ccdbb671a4.npy",
      "sha256": "bcf7fa8cd399bbb2382914ed3df5cb7335aa3ec29fec2c73fe6d7025e28a18db",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.17.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "18f1395b23d1597948224b434838c9d3c6ea490a90322537b8b3e68a8426c7ed.npy",
      "sha256": "d18f0a7ce033cb784a5f6ffc4817b78d57f1fb179b45a9c896a180fbf2ff3eb1",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-33eebedccdeb74903e4c6900686def3c3b74ade655a09773d0491b31d56ff529",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7068965517241379,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 49,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.49137931034482757,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第40轮

**当时目的与操作理由（原文）**

Round 40 of 50: scale decoder input_layernorm.weight in layers 12-17 by 1.05 from W0. Opposite-direction control to round 39, whose 0.95 scaling repaired eight responses without correctness regressions and reached 57/116 B0 and 65/116 B1 wording-averaged joint correctness. Tests direction-specific middle attention-input sensitivity rather than assuming attenuation is causally beneficial. All other parameters restored to W0; uniform scaling only.

**本轮原记录的主分数**：`0.46551724137931033`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-f4ced7faa74d5eb0aed825268dd0ced0a65d39d6d51b6f67996cb0440d73a1ae",
  "l2": 2.891918614612851,
  "parent": "c-33eebedccdeb74903e4c6900686def3c3b74ade655a09773d0491b31d56ff529",
  "rationale": "Round 40 of 50: scale decoder input_layernorm.weight in layers 12-17 by 1.05 from W0. Opposite-direction control to round 39, whose 0.95 scaling repaired eight responses without correctness regressions and reached 57/116 B0 and 65/116 B1 wording-averaged joint correctness. Tests direction-specific middle attention-input sensitivity rather than assuming attenuation is causally beneficial. All other parameters restored to W0; uniform scaling only.",
  "tensors": {
    "model.language_model.layers.12.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "e57f2ba1dd92e4a12b6cb857f22dae6a82f8de0b8703535bc51543485e079b22.npy",
      "sha256": "903ed309f527aa3a6e5afb010cbda5c47ebccde9e18ed025d4a9b25ea2976f45",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.13.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "028ac9c30d8e1e9060986a456afde270a51d39a590ec017f0a8af6971f6a9539.npy",
      "sha256": "a3e4713b04d1bbbf4a33bf4660ea4b958d3960242cf43b41471749dbd438edee",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.14.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "81723cc2bda8566eca79b387adb6a32f9a1657b727b93cd3e6c1ec56cee125d7.npy",
      "sha256": "518476e9a115d188ae583e8c6f166f6771bd7bc45fbc8df7d4528e183c7cd4cd",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.15.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f5048c39ae1fe62ea97fcc03d65cf73c355d27080918af6be3bcd045d9053a43.npy",
      "sha256": "29894293b2f3966f3eabd38338f0c43845cd099c1f18debb424f750788a59374",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.16.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b2561341cf7a992be6fe49fecf46a8e3be0de6e1d3009aab60a7b5ccdbb671a4.npy",
      "sha256": "231ecae4bd15325ee3a74725e98b725ad81da50f541a5fdf3c460e222d1d96c9",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.17.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "18f1395b23d1597948224b434838c9d3c6ea490a90322537b8b3e68a8426c7ed.npy",
      "sha256": "23b159c6f5c7a9c1cc7866f19a3ab11360be891817c4aacd87befecd7f7ec049",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f4ced7faa74d5eb0aed825268dd0ced0a65d39d6d51b6f67996cb0440d73a1ae",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6918103448275862,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.46551724137931033,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第41轮

**当时目的与操作理由（原文）**

Round 41 of 50: scale norm1.weight and norm1.bias in vision blocks 18-23 by 0.95 from W0. Tests late vision attention-input gain separately from decoder normalization and merger interventions. All other parameters restored to W0; uniform scaling only, with no per-coordinate fitting. Planned opposite-direction control at 1.05.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 12288,
  "id": "c-1d46f766d0a57b4848a2927dff641b6c18b91a1e4f78ff72a586263c188e9948",
  "l2": 5.712896918869039,
  "parent": "c-f4ced7faa74d5eb0aed825268dd0ced0a65d39d6d51b6f67996cb0440d73a1ae",
  "rationale": "Round 41 of 50: scale norm1.weight and norm1.bias in vision blocks 18-23 by 0.95 from W0. Tests late vision attention-input gain separately from decoder normalization and merger interventions. All other parameters restored to W0; uniform scaling only, with no per-coordinate fitting. Planned opposite-direction control at 1.05.",
  "tensors": {
    "model.visual.blocks.18.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "b575497ceb507c54841b2c8f0910f61ff981bc9209aa98a901492f1fedc1568f.npy",
      "sha256": "b94d46c8e834b8285e84e72abfce694b5d4582bd5ae2f7f9f7f31f5ba5c9765d",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.18.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "2b11bb341b8a0a02ef5b45d585557a905e82ae949ef710fea333ddef7b7b6c4f.npy",
      "sha256": "e50572ea37fb7b27d127a4f53547a7960a9347a45f207dde8ec3b2421c10df01",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.19.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "19ab65bf539a0a863b28211bce2712c25800e526e1d8f2b9987702f477225431.npy",
      "sha256": "a894f8061a63dc450803036d8fb51665390fa92db917544be81656fa0845ab4c",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.19.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "5f3b7cb7acb6ca7c59916f018d87b6b8a46915a3f2dd0036cb7847f501edf7e3.npy",
      "sha256": "b062a52f36a1d64f7b75d2edaee447bd70d2c915876094ae128e20141e33e727",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.20.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "a2573d3817b5a6f31d33773620ef9c0e4bff6dd3443609cfa27fb86ab85c817a.npy",
      "sha256": "3bdefec09192b31969d4815bb6eee66326f88f66949476ab21e8bdf87b71059a",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.20.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "9311c117a1bccff9c49d56e4e031397dd6cf095fba79a43a2c694fc75c4b7fc5.npy",
      "sha256": "cb4c4c1b4a015e563b76fdfe8a6ff6e0415680c806e2e126167f7523ba2f0188",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.21.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "0fefabafe3390c0280d5a1a308743575e7b44e32470362dcdcdefb978e054291.npy",
      "sha256": "859c7a6d66db296622bf30c5765e2ba9cf9d342cf6a5755e260f5b160ebf2b04",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.21.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "e59e277b5bc34a62d81fd5a9290ea0021b2f2d90afffb51af2ed7e7f625f0bb2.npy",
      "sha256": "a0401edebdd2179f02287d7c18b40b505792a0a6017cbc053c844f48566d53fd",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.22.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1e70a55ab0135213e4df5d97cae22649952279741a224f28bf682e28cbad1f46.npy",
      "sha256": "06be2379f1eb6f17f1ed8e89a2563c6e44883b13ca534d7b690624c28503d624",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.22.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "46ce4189e62e34a5b9ffd6884858d8bd30b0fa355332b3b846bb961241ae51d0.npy",
      "sha256": "d1f1d1af5ae771eeb8a9d9df7156aa359872db0457461b9c16cf1debc67e492a",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.23.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "57f63f56a91da86fedee32dc4669a65d256af004f57a99a266442a30359922ae.npy",
      "sha256": "f3c98a6041af1ba065966870a59bbdbe268648d57f1f12aaf718b44cd4599eea",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.23.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "44059d8c29dfc19ebe62c475d9ef18ad746182fb8fde07c2b9bed2deb6d6fe52.npy",
      "sha256": "5d1bf3a527400e2b1a4dab5ad26949548733a6d276fb9337be4d48419dbae75f",
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
  "candidate": "c-1d46f766d0a57b4848a2927dff641b6c18b91a1e4f78ff72a586263c188e9948",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6939655172413793,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 45,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第42轮

**当时目的与操作理由（原文）**

Round 42 of 50: scale norm1.weight and norm1.bias in vision blocks 18-23 by 1.05 from W0. Opposite-direction control to round 41's 0.95 scaling, which yielded eight repairs and six regressions, B0 joint correctness 55/116, and passed the protected-cell thresholds. All other parameters restored to W0; uniform scaling only.

**本轮原记录的主分数**：`0.4827586206896552`；保留原始0–1尺度。

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
  "changed_scalars": 12288,
  "id": "c-e2f5ff2e4f8f59d0937bd57b6c554f8940339c3eb560d0ac28494cd57da6d1d2",
  "l2": 5.70338972712628,
  "parent": "c-1d46f766d0a57b4848a2927dff641b6c18b91a1e4f78ff72a586263c188e9948",
  "rationale": "Round 42 of 50: scale norm1.weight and norm1.bias in vision blocks 18-23 by 1.05 from W0. Opposite-direction control to round 41's 0.95 scaling, which yielded eight repairs and six regressions, B0 joint correctness 55/116, and passed the protected-cell thresholds. All other parameters restored to W0; uniform scaling only.",
  "tensors": {
    "model.visual.blocks.18.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "b575497ceb507c54841b2c8f0910f61ff981bc9209aa98a901492f1fedc1568f.npy",
      "sha256": "741884cad72d837c67f525d08662ae660774ad1eeaa04112122ea781b0d16bfb",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.18.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "2b11bb341b8a0a02ef5b45d585557a905e82ae949ef710fea333ddef7b7b6c4f.npy",
      "sha256": "cefc8bd31b3ccfec14c7c80c404a9c19457c5da040dae977fa1a23789b3cc469",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.19.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "19ab65bf539a0a863b28211bce2712c25800e526e1d8f2b9987702f477225431.npy",
      "sha256": "a666d0853452e173d1c83b25555c1fbdcf7da26fde4309abda1c97c9b35c508a",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.19.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "5f3b7cb7acb6ca7c59916f018d87b6b8a46915a3f2dd0036cb7847f501edf7e3.npy",
      "sha256": "d3cfc09145a47117ff38f69ad7cec437e940da139e9d2cf5c3a1666cb8f3eb76",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.20.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "a2573d3817b5a6f31d33773620ef9c0e4bff6dd3443609cfa27fb86ab85c817a.npy",
      "sha256": "48cbd953a305c29e55f741d6143e4a5c392e850492fe40c10df8e00e98141aec",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.20.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "9311c117a1bccff9c49d56e4e031397dd6cf095fba79a43a2c694fc75c4b7fc5.npy",
      "sha256": "be9e69a511e3a31375230b9c8240e41f07c6dc200cc851b84cd19bc72022ccad",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.21.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "0fefabafe3390c0280d5a1a308743575e7b44e32470362dcdcdefb978e054291.npy",
      "sha256": "2c7c104ea3762b468019d16fa4d38c1aabf601d74300e83253afba7be1c17f18",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.21.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "e59e277b5bc34a62d81fd5a9290ea0021b2f2d90afffb51af2ed7e7f625f0bb2.npy",
      "sha256": "bf85cb26897a89119370d12a8dea7cd778051788635d186b339ebcc2ad74ed37",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.22.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "1e70a55ab0135213e4df5d97cae22649952279741a224f28bf682e28cbad1f46.npy",
      "sha256": "38389d8f8c4f59452e091c1f7e8851e9e37874f72e51bf9f0246a44bcd05c54b",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.22.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "46ce4189e62e34a5b9ffd6884858d8bd30b0fa355332b3b846bb961241ae51d0.npy",
      "sha256": "4d0d258d065f72ed04d1d03488612c9e48fea692a3984d0dda28abcc7982dc90",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.23.norm1.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "57f63f56a91da86fedee32dc4669a65d256af004f57a99a266442a30359922ae.npy",
      "sha256": "ec135d6602fc61418fbf7d2da3028da318aa1ad17e6a457fa0ac9d82682835dd",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.23.norm1.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "44059d8c29dfc19ebe62c475d9ef18ad746182fb8fde07c2b9bed2deb6d6fe52.npy",
      "sha256": "e995350b3050446778ca9ac03b7f4dbffc3dd716ba3f4ec9ab33188468f49ce0",
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
  "candidate": "c-e2f5ff2e4f8f59d0937bd57b6c554f8940339c3eb560d0ac28494cd57da6d1d2",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6982758620689655,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 50,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.4827586206896552,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第43轮

**当时目的与操作理由（原文）**

Round 43 of 50: scale norm2.weight and norm2.bias in vision blocks 18-23 by 0.95 from W0. Tests late vision MLP-input gain against the attention-input interventions in rounds 41-42, using the same number of normalization coordinates. All other parameters restored to W0; uniform scaling only. Planned opposite-direction control at 1.05.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 12288,
  "id": "c-bb30e30a832b1e6e6bafac9e08cb269f2603f3318222e382521555909c256744",
  "l2": 42.18311188485411,
  "parent": "c-e2f5ff2e4f8f59d0937bd57b6c554f8940339c3eb560d0ac28494cd57da6d1d2",
  "rationale": "Round 43 of 50: scale norm2.weight and norm2.bias in vision blocks 18-23 by 0.95 from W0. Tests late vision MLP-input gain against the attention-input interventions in rounds 41-42, using the same number of normalization coordinates. All other parameters restored to W0; uniform scaling only. Planned opposite-direction control at 1.05.",
  "tensors": {
    "model.visual.blocks.18.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "440e017ed74b30a063f9c8d9dbd8ef7e51e0cff298332aca7fd7c86bf4f4106c.npy",
      "sha256": "6ce9419b0d42d5d519c9e7c728a17fe44feed27aa357ca8e473fa64b02c47c5f",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.18.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "abe85a513344c03140a5b29dbd37ffa383058f3c33389b4c535039a97aa7d719.npy",
      "sha256": "dfb92bb24bef7bc44fd46948b32d34588555d7cbf3e55bda28e08e0ddc12c284",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.19.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "5d8b03e076a453aa62b8b50783c6ddb55dbb8ce2b233a4282e97b42269fbda5e.npy",
      "sha256": "867cbea3557ec3a92e9e7155d4d015e15c146c988e9a3e949e0e350fbf88303f",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.19.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "c6c5ced6d4af07447d5446a0b0b9022af61f1bbc6d1c69bfd0c4d6bac0a0a214.npy",
      "sha256": "e3aa4bf778601cd788857a7c7e4413429175fa6a19e3a412512508ee41dc5cda",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.20.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "5b80b532fe81ef8dde12686bd10bf3ac8217fc5538d2aca13ac55f9f23e48e99.npy",
      "sha256": "0d45bef191cdcbd12c74ece091061418584fe9114a811e240c349de0deb2a10d",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.20.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "bb631482156fd201b1638dcb01114dcca1dd343b9a1c42cb36aa4937654504d5.npy",
      "sha256": "521029cc701a3c0a66285875108cea7b7a3fe8dd8c10e4bc5941b9a2e3720d35",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.21.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "8e64b7ef7afc5d7118b2fd12344a09fe60b87966724db2a8d25e69ff8b7779b5.npy",
      "sha256": "e683e2322d598e05e9ff6dba2498891eeda3562dfb22451ef954e2534acc1a85",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.21.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "136e667f368dd079a6044a7b7b657c36c85fe82daa9f9e6255667f88b879804e.npy",
      "sha256": "ba7bd11950d0afcc1028a9fbafa0fb27c516a1d940947784f0c59f6fbd533a5e",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.22.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "72ea044e7ff8a7181aeb648e5ff95eaacb387d99aa52fe81d9e69c6e422998d4.npy",
      "sha256": "6f93ca5495ba6899baf38d23af35a36eafc3729e68b301b0de5f814a11d05a4b",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.22.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "7da21fdc18ff8fa13af4f83dfb262837d1251cfb83dccd8765b8f7de2ac0b7af.npy",
      "sha256": "58cbe841dc855a053a22444da95e7374937797a21a2952b60b4f4c9bb83a022d",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.23.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "bacecb67d554fb53da07326ab8920dae7975b59b797d09571e2fe3f459134f37.npy",
      "sha256": "33e9903c33c2cd977b994e6153ff595716ee82a56c549cad727fef804b9e6f03",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.23.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "b999a793a5a1d1d269020a9b990b6b9f2691735c261bfe9f628d4353612504e6.npy",
      "sha256": "1e4462516ac3793443ab0754a4671af836028a2298d3ae70b3bd02c6e91fcf98",
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
  "candidate": "c-bb30e30a832b1e6e6bafac9e08cb269f2603f3318222e382521555909c256744",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6939655172413793,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第44轮

**当时目的与操作理由（原文）**

Round 44 of 50: scale norm2.weight and norm2.bias in vision blocks 18-23 by 1.05 from W0. Opposite-direction control to round 43's 0.95 scaling, which produced three repairs and one regression while retaining B0 joint correctness of 55/116. All other parameters restored to W0; uniform scaling only.

**本轮原记录的主分数**：`0.49137931034482757`；保留原始0–1尺度。

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
  "changed_scalars": 12288,
  "id": "c-869c3e8e145ca307e22cd2677ad45ab9c344d553e3f2b161198d85f4d73e29dd",
  "l2": 42.145489545414,
  "parent": "c-bb30e30a832b1e6e6bafac9e08cb269f2603f3318222e382521555909c256744",
  "rationale": "Round 44 of 50: scale norm2.weight and norm2.bias in vision blocks 18-23 by 1.05 from W0. Opposite-direction control to round 43's 0.95 scaling, which produced three repairs and one regression while retaining B0 joint correctness of 55/116. All other parameters restored to W0; uniform scaling only.",
  "tensors": {
    "model.visual.blocks.18.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "440e017ed74b30a063f9c8d9dbd8ef7e51e0cff298332aca7fd7c86bf4f4106c.npy",
      "sha256": "4e8c18c233f7fd60eb7f8e3931d6ac9c7770bbc864b2099a2773c8304555e90f",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.18.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "abe85a513344c03140a5b29dbd37ffa383058f3c33389b4c535039a97aa7d719.npy",
      "sha256": "345a1a7b7e50520d4d2ded9a2927238bfe25d9a8c28a4b857270f422db5870a5",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.19.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "5d8b03e076a453aa62b8b50783c6ddb55dbb8ce2b233a4282e97b42269fbda5e.npy",
      "sha256": "510df5a75de01580bd8c8b4824d286da0c6803971b1fc47a84a385d775262a5e",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.19.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "c6c5ced6d4af07447d5446a0b0b9022af61f1bbc6d1c69bfd0c4d6bac0a0a214.npy",
      "sha256": "a59194c06dc726e7e156fd8a04e5d8013a92b7ca9872bac562ce4ecd97345977",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.20.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "5b80b532fe81ef8dde12686bd10bf3ac8217fc5538d2aca13ac55f9f23e48e99.npy",
      "sha256": "999b50202e0382fac8f3440aafc71f23d0d363f289e7db5aabc7f6b21447e4cb",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.20.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "bb631482156fd201b1638dcb01114dcca1dd343b9a1c42cb36aa4937654504d5.npy",
      "sha256": "f117ef9a184b6a895e26d4d2388fb21ae3d47671460c21c8c00c2d04691da058",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.21.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "8e64b7ef7afc5d7118b2fd12344a09fe60b87966724db2a8d25e69ff8b7779b5.npy",
      "sha256": "919cc763ee2d58f840664e974fc7971e7e672359b398169013ac40e10067c4f4",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.21.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "136e667f368dd079a6044a7b7b657c36c85fe82daa9f9e6255667f88b879804e.npy",
      "sha256": "66eb431c3e09f0fa91c58a95416ae67fbce456e35ccfe51a805ad8dcbd09df48",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.22.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "72ea044e7ff8a7181aeb648e5ff95eaacb387d99aa52fe81d9e69c6e422998d4.npy",
      "sha256": "fa769b896c5c5caa5dc4bfbf3b96abc5026023490c39d46618441beee5127273",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.22.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "7da21fdc18ff8fa13af4f83dfb262837d1251cfb83dccd8765b8f7de2ac0b7af.npy",
      "sha256": "6c1edd8a8fe1228ef33ad225065956869286f0453daf2c6ecc082ca30abac932",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.23.norm2.bias": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "bacecb67d554fb53da07326ab8920dae7975b59b797d09571e2fe3f459134f37.npy",
      "sha256": "b6890f9a734502cb972928817cb3fa6070a91b6a4ee8e4e0ce7bf795b2224077",
      "shape": [
        1024
      ]
    },
    "model.visual.blocks.23.norm2.weight": {
      "changed": 1024,
      "dtype": "BF16",
      "file": "b999a793a5a1d1d269020a9b990b6b9f2691735c261bfe9f628d4353612504e6.npy",
      "sha256": "92b8376962da13a4f327c98d9756587964c4e766a7f0634ec5ca7fd10f7c494a",
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
  "candidate": "c-869c3e8e145ca307e22cd2677ad45ab9c344d553e3f2b161198d85f4d73e29dd",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6982758620689655,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.49137931034482757,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第45轮

**当时目的与操作理由（原文）**

Round 45 of 50: scale self_attn.q_norm.weight in decoder layers 12-23 by 1.025 from W0. Lower-dose comparison to round 23's selected 1.05 scaling, which achieved 58/116 B0 joint correctness but introduced six individual correctness regressions. Tests whether a weaker perturbation retains gains or reduces regressions. All other parameters restored to W0; uniform scaling only. Planned intermediate-dose comparison at 1.075.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 1536,
  "id": "c-f69c7426650b7455434e0343208730ef08b1a372e1e2f31d9a81afa65b9ef225",
  "l2": 1.7236705641826797,
  "parent": "c-869c3e8e145ca307e22cd2677ad45ab9c344d553e3f2b161198d85f4d73e29dd",
  "rationale": "Round 45 of 50: scale self_attn.q_norm.weight in decoder layers 12-23 by 1.025 from W0. Lower-dose comparison to round 23's selected 1.05 scaling, which achieved 58/116 B0 joint correctness but introduced six individual correctness regressions. Tests whether a weaker perturbation retains gains or reduces regressions. All other parameters restored to W0; uniform scaling only. Planned intermediate-dose comparison at 1.075.",
  "tensors": {
    "model.language_model.layers.12.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0e5a902a6b36715df7b33bc20beb3f047f743c1f188dbfb7b97819905c65456c.npy",
      "sha256": "ed38cccf9cca6dc17ac3f0bf6f33ce708a1fc08dab43c9f506b26e99a4094301",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.13.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0c8eb283bbabad1e3f9d3953227c163d7a8fb0d0ed046f4e911ac7d4a6161335.npy",
      "sha256": "612d671fa7c1b88d7c79fd39ced9da053b268a4dd4282f7704786e051ffd38c9",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.14.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "d2544ee68d66946d23d977827c24cbae5d1c76907dc2a0d7ff3f45993606ff37.npy",
      "sha256": "4312ef08a891fa94029b805a5e6f7acab90a7975abdeae680a9befb70361b114",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.15.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "017366cbb50180df94356b01c53217d02aaec84f8b0056b58fd3d777dbb895a5.npy",
      "sha256": "930c5d3374be15b773426bb4db1851baa24b818a147381dee08e175f7d526b54",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.16.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9ea551be1b29a5eeb9e87f5601d7cfc7bb5ccb6cac29c44b5998874c4b73b2c7.npy",
      "sha256": "68f085d26a3c3bad4bded0592418275006b9c3111659cf31321e9367c5fad2c6",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.17.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c7d7331485a2d5a52e2415034ac56a0c44e89ccf7a20a5b41a769181147ffdba.npy",
      "sha256": "2f1104cd0246a144c0b4f34ee157d7c333efa3157a405417d9c48561a92be912",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.18.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "53b569f6a8c75e8ca7c16bcd6cd489da5812822c17b7376eb953ed71ebc98aa6.npy",
      "sha256": "1911aa12daadfb2adb652976091053e9dfc46975f9a7f58695f6cc7461b6db63",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.19.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "cfcb958acbc47f6a0c6ba6514bf424d4ebf1e65e05e99e266ce55601422aaa0d.npy",
      "sha256": "603316d44d862c96e3a53535c1c96c10ee7b75bb6a6430d17322aa85a7e88add",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.20.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "2d383293b38ed94a9ebe762db87adf6905c88e830ea656633fbb49c557cc77d6.npy",
      "sha256": "73ad4acee2d4264d89df0cbbcaee2c68f4fc6948994b3738422e2090884dbd36",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.21.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "3438a2fc73755d660a160c20895b0a6da0495946cae579b995cd40f5e928a9dc.npy",
      "sha256": "605a3528f96ad4bbffa3b361be6373edfcc1343a51da5267723520f69873923a",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.22.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6c141e33c8c72c1b73364682db8aafa901bf1243285958c5635cb193a6c2ae36.npy",
      "sha256": "e4d8ee1f8d795e7c610296846c6b3483228a3fab92af9525af0a48fa7b31ca12",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.23.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "5c78ddbde110190e8894318b7ee805830f8c18f013b9719c1345f374eacf6619.npy",
      "sha256": "b7f270221ad0cfaca91ce589f06b9c27d45fdb9a92121ddd55f228a24922980e",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f69c7426650b7455434e0343208730ef08b1a372e1e2f31d9a81afa65b9ef225",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6939655172413793,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第46轮

**当时目的与操作理由（原文）**

Round 46 of 50: scale self_attn.q_norm.weight in decoder layers 12-23 by 1.075 from W0. Intermediate-dose comparison with previously evaluated 1.025, 1.05, and 1.10 scalings. Round 45's 1.025 scaling yielded five repairs and three regressions, with B0 wording-averaged joint correctness of 55/116. Test whether the intermediate dose improves joint correctness while satisfying all protected-cell thresholds. All other parameters restored to W0; uniform scaling only.

**本轮原记录的主分数**：`0.5086206896551724`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-828d2d79909785f4c02ae9fc50c82ac14a70c1dcb077b28596d729a377758d6f",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.5086206896551724
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 1536,
  "id": "c-828d2d79909785f4c02ae9fc50c82ac14a70c1dcb077b28596d729a377758d6f",
  "l2": 5.209685486842848,
  "parent": "c-f69c7426650b7455434e0343208730ef08b1a372e1e2f31d9a81afa65b9ef225",
  "rationale": "Round 46 of 50: scale self_attn.q_norm.weight in decoder layers 12-23 by 1.075 from W0. Intermediate-dose comparison with previously evaluated 1.025, 1.05, and 1.10 scalings. Round 45's 1.025 scaling yielded five repairs and three regressions, with B0 wording-averaged joint correctness of 55/116. Test whether the intermediate dose improves joint correctness while satisfying all protected-cell thresholds. All other parameters restored to W0; uniform scaling only.",
  "tensors": {
    "model.language_model.layers.12.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0e5a902a6b36715df7b33bc20beb3f047f743c1f188dbfb7b97819905c65456c.npy",
      "sha256": "df125a183558aff8ba75876b413bd33d9a5714e79dbf87ce2562dac2ff45209d",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.13.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0c8eb283bbabad1e3f9d3953227c163d7a8fb0d0ed046f4e911ac7d4a6161335.npy",
      "sha256": "758a6e94bf9f91718bbb5365686f3dc6198da35022b89796de99fcd0128603e3",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.14.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "d2544ee68d66946d23d977827c24cbae5d1c76907dc2a0d7ff3f45993606ff37.npy",
      "sha256": "d54ebe35cf3b556f13e64b1b6cec1551af7dfcf97753a943040a81de4bd63274",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.15.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "017366cbb50180df94356b01c53217d02aaec84f8b0056b58fd3d777dbb895a5.npy",
      "sha256": "aec53e373e128c4f733bc2bc9d5017889c2c66268a65dad3aac3a526dc85ade6",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.16.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9ea551be1b29a5eeb9e87f5601d7cfc7bb5ccb6cac29c44b5998874c4b73b2c7.npy",
      "sha256": "65bcb7720703419be6ddd2d49a54ca0b3339b03a5911d84b5f86a630f64a9d3b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.17.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c7d7331485a2d5a52e2415034ac56a0c44e89ccf7a20a5b41a769181147ffdba.npy",
      "sha256": "aeefa6f6fda9f97e35b856e7fae4401fd627dc7cbe89dd046796195717f9616b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.18.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "53b569f6a8c75e8ca7c16bcd6cd489da5812822c17b7376eb953ed71ebc98aa6.npy",
      "sha256": "d8dfc0585279221aa9cc1ec8b93177e83cd48675a9ec83ae5c9318100acff637",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.19.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "cfcb958acbc47f6a0c6ba6514bf424d4ebf1e65e05e99e266ce55601422aaa0d.npy",
      "sha256": "a635d1d157cd5245a90ee599f8ebbc2b3f4ef6c6dd0c68ae546296705476aee5",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.20.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "2d383293b38ed94a9ebe762db87adf6905c88e830ea656633fbb49c557cc77d6.npy",
      "sha256": "bf47f8bc46e5a655e179466938e978656c820d79f1059db78b2f19e0ef9164ff",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.21.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "3438a2fc73755d660a160c20895b0a6da0495946cae579b995cd40f5e928a9dc.npy",
      "sha256": "9e2436973b89336eedabc1a7f6dd9ebac9ea46f7d33cdddad0cec2bbfe846de4",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.22.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6c141e33c8c72c1b73364682db8aafa901bf1243285958c5635cb193a6c2ae36.npy",
      "sha256": "e9c08a8ff0051325828e50ff20740edf96dadde2c0ea0875d4bf28a9ed5955ad",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.23.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "5c78ddbde110190e8894318b7ee805830f8c18f013b9719c1345f374eacf6619.npy",
      "sha256": "977bd2cb772248bf670534c54e1159c8a02f9dec46c2530e1d473de3c529b905",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-828d2d79909785f4c02ae9fc50c82ac14a70c1dcb077b28596d729a377758d6f",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6896551724137931,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.4827586206896552,
    "repair_score": 0.5086206896551724,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第47轮

**当时目的与操作理由（原文）**

Round 47 of 50: scale decoder input_layernorm.weight in layers 12-17 by 0.90 from W0. Stronger-attenuation dose comparison to round 39's 0.95 scaling, which repaired eight responses without correctness regressions and achieved B0 joint correctness of 57/116. Tests whether the benefit persists or reverses at twice the nominal attenuation. All query-normalization edits and other parameters restored to W0; uniform scaling only. Planned weaker-attenuation comparison at 0.975.

**本轮原记录的主分数**：`0.5086206896551724`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-56a75408a1c271fc3b32fb0a77de2821c8235183181c14eca9dd0df5308550aa",
  "l2": 5.787386220386196,
  "parent": "c-828d2d79909785f4c02ae9fc50c82ac14a70c1dcb077b28596d729a377758d6f",
  "rationale": "Round 47 of 50: scale decoder input_layernorm.weight in layers 12-17 by 0.90 from W0. Stronger-attenuation dose comparison to round 39's 0.95 scaling, which repaired eight responses without correctness regressions and achieved B0 joint correctness of 57/116. Tests whether the benefit persists or reverses at twice the nominal attenuation. All query-normalization edits and other parameters restored to W0; uniform scaling only. Planned weaker-attenuation comparison at 0.975.",
  "tensors": {
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
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-56a75408a1c271fc3b32fb0a77de2821c8235183181c14eca9dd0df5308550aa",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7176724137931034,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 49,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 33,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 50,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 49,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.5172413793103449,
    "repair_score": 0.5086206896551724,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第48轮

**当时目的与操作理由（原文）**

Round 48 of 50: scale decoder input_layernorm.weight in layers 12-17 by 0.975 from W0. Planned weaker-attenuation comparison with round 39 at 0.95 and round 47 at 0.90. Round 47 achieved B0 joint correctness of 59/116 and 13 individual repairs without correctness regressions; test whether weaker attenuation retains these benefits. All other parameters restored to W0; uniform scaling only.

**本轮原记录的主分数**：`0.47413793103448276`；保留原始0–1尺度。

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
  "changed_scalars": 15360,
  "id": "c-f0cae4bc8a454cb6add0cfe1712336ef8371d5b57313fbb6ab56f4c69a1485c9",
  "l2": 1.4452554846162826,
  "parent": "c-56a75408a1c271fc3b32fb0a77de2821c8235183181c14eca9dd0df5308550aa",
  "rationale": "Round 48 of 50: scale decoder input_layernorm.weight in layers 12-17 by 0.975 from W0. Planned weaker-attenuation comparison with round 39 at 0.95 and round 47 at 0.90. Round 47 achieved B0 joint correctness of 59/116 and 13 individual repairs without correctness regressions; test whether weaker attenuation retains these benefits. All other parameters restored to W0; uniform scaling only.",
  "tensors": {
    "model.language_model.layers.12.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "e57f2ba1dd92e4a12b6cb857f22dae6a82f8de0b8703535bc51543485e079b22.npy",
      "sha256": "f362269c5c8d54888edb19776574ab994c3153bb43b49ad001194a97d4ce619d",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.13.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "028ac9c30d8e1e9060986a456afde270a51d39a590ec017f0a8af6971f6a9539.npy",
      "sha256": "a5f5790ea5a3c273bf3f06d6d971dbd53ee49bbbd175c318aac4ac0f627ecefb",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.14.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "81723cc2bda8566eca79b387adb6a32f9a1657b727b93cd3e6c1ec56cee125d7.npy",
      "sha256": "eddb0d0282b623f778071737e62950daf91a083c8189f8ece1d03eff9c83f9b0",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.15.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "f5048c39ae1fe62ea97fcc03d65cf73c355d27080918af6be3bcd045d9053a43.npy",
      "sha256": "b178ffc253ef4fd7c91ede051669fbb5fecf82ad2a7fc476d08f8ca622aa6d2b",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.16.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "b2561341cf7a992be6fe49fecf46a8e3be0de6e1d3009aab60a7b5ccdbb671a4.npy",
      "sha256": "933f5f09203ee2bbc9b812a7c66b3eba4ab85c9fb622822f43efbfb452f4c48c",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.17.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "18f1395b23d1597948224b434838c9d3c6ea490a90322537b8b3e68a8426c7ed.npy",
      "sha256": "0a8e7852f02efc5b79b26c60cca4d2daccd148d34b0acf8526f86d67945c48c5",
      "shape": [
        2560
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-f0cae4bc8a454cb6add0cfe1712336ef8371d5b57313fbb6ab56f4c69a1485c9",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6961206896551724,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 36,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 49,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.46551724137931033,
    "repair_score": 0.47413793103448276,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第49轮

**当时目的与操作理由（原文）**

Round 49 of 50: combine round 47's decoder input_layernorm.weight scaling of 0.90 in layers 12-17 with round 17's auxiliary merger 0 norm.weight scaling of 0.75, both relative to W0. Leave the auxiliary norm bias unchanged. The standalone components achieved B0 joint correctness of 59/116 and 58/116 respectively, without individual correctness regressions. Test complementarity versus interference rather than assuming additive gains. All other parameters restored to W0; uniform scaling only.

**本轮原记录的主分数**：`0.5086206896551724`；保留原始0–1尺度。

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
  "changed_scalars": 19456,
  "id": "c-ff24dcc258efb9e5eef35b263d302fa9e0117f4a55fec89b29a7c5722e8840ea",
  "l2": 17.185645429950956,
  "parent": "c-f0cae4bc8a454cb6add0cfe1712336ef8371d5b57313fbb6ab56f4c69a1485c9",
  "rationale": "Round 49 of 50: combine round 47's decoder input_layernorm.weight scaling of 0.90 in layers 12-17 with round 17's auxiliary merger 0 norm.weight scaling of 0.75, both relative to W0. Leave the auxiliary norm bias unchanged. The standalone components achieved B0 joint correctness of 59/116 and 58/116 respectively, without individual correctness regressions. Test complementarity versus interference rather than assuming additive gains. All other parameters restored to W0; uniform scaling only.",
  "tensors": {
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
    "model.visual.deepstack_merger_list.0.norm.weight": {
      "changed": 4096,
      "dtype": "BF16",
      "file": "d2a657854a6805ff82f1dc61de1f8c92f4beb8ff87205e9a2310f345c9055bd1.npy",
      "sha256": "fc430fe41a80cb67a85d7214e4f82e6ecee623b51e388f0ca0b89dd337ebfa58",
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
  "candidate": "c-ff24dcc258efb9e5eef35b263d302fa9e0117f4a55fec89b29a7c5722e8840ea",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.7068965517241379,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 32,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 48,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 48,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.5,
    "repair_score": 0.5086206896551724,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

## 第50轮

**当时目的与操作理由（原文）**

Round 50 of 50: combine round 46's self_attn.q_norm.weight scaling of 1.075 in decoder layers 12-23 with round 47's input_layernorm.weight scaling of 0.90 in decoder layers 12-17, both relative to W0. Both standalone components achieved B0 joint correctness of 59/116, but their accuracy and regression profiles differed substantially. Test whether the combined intervention preserves complementary repairs or introduces interference. Restore the auxiliary merger and every other parameter to W0. Uniform scaling only; this is the final planned unique candidate.

**本轮原记录的主分数**：`0.5258620689655172`；保留原始0–1尺度。

**选优/保护结果**

```json
{
  "best": "c-81dd85b39a266ffe7352e0792bf026051cb849eb066dc6276365d0bdd2b9c4d4",
  "development_only": true,
  "independent_confirmation": false,
  "repair_score": 0.5258620689655172
}
```

**完整候选定义（基线、位置、改动数量、幅度、张量身份）**

```json
{
  "base": "w0-72b28080bcd9951ceeeebfb62a5fd532cb3d52e4714ea3baedea3796b650ed06",
  "changed_scalars": 16896,
  "id": "c-81dd85b39a266ffe7352e0792bf026051cb849eb066dc6276365d0bdd2b9c4d4",
  "l2": 7.7868261914426355,
  "parent": "c-ff24dcc258efb9e5eef35b263d302fa9e0117f4a55fec89b29a7c5722e8840ea",
  "rationale": "Round 50 of 50: combine round 46's self_attn.q_norm.weight scaling of 1.075 in decoder layers 12-23 with round 47's input_layernorm.weight scaling of 0.90 in decoder layers 12-17, both relative to W0. Both standalone components achieved B0 joint correctness of 59/116, but their accuracy and regression profiles differed substantially. Test whether the combined intervention preserves complementary repairs or introduces interference. Restore the auxiliary merger and every other parameter to W0. Uniform scaling only; this is the final planned unique candidate.",
  "tensors": {
    "model.language_model.layers.12.input_layernorm.weight": {
      "changed": 2560,
      "dtype": "BF16",
      "file": "e57f2ba1dd92e4a12b6cb857f22dae6a82f8de0b8703535bc51543485e079b22.npy",
      "sha256": "2b3cad2bfb725ba639beb63e762967ed802e964f2aa3d9db249cd007115c53c8",
      "shape": [
        2560
      ]
    },
    "model.language_model.layers.12.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0e5a902a6b36715df7b33bc20beb3f047f743c1f188dbfb7b97819905c65456c.npy",
      "sha256": "df125a183558aff8ba75876b413bd33d9a5714e79dbf87ce2562dac2ff45209d",
      "shape": [
        128
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
    "model.language_model.layers.13.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "0c8eb283bbabad1e3f9d3953227c163d7a8fb0d0ed046f4e911ac7d4a6161335.npy",
      "sha256": "758a6e94bf9f91718bbb5365686f3dc6198da35022b89796de99fcd0128603e3",
      "shape": [
        128
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
    "model.language_model.layers.14.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "d2544ee68d66946d23d977827c24cbae5d1c76907dc2a0d7ff3f45993606ff37.npy",
      "sha256": "d54ebe35cf3b556f13e64b1b6cec1551af7dfcf97753a943040a81de4bd63274",
      "shape": [
        128
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
    "model.language_model.layers.15.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "017366cbb50180df94356b01c53217d02aaec84f8b0056b58fd3d777dbb895a5.npy",
      "sha256": "aec53e373e128c4f733bc2bc9d5017889c2c66268a65dad3aac3a526dc85ade6",
      "shape": [
        128
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
    "model.language_model.layers.16.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "9ea551be1b29a5eeb9e87f5601d7cfc7bb5ccb6cac29c44b5998874c4b73b2c7.npy",
      "sha256": "65bcb7720703419be6ddd2d49a54ca0b3339b03a5911d84b5f86a630f64a9d3b",
      "shape": [
        128
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
    "model.language_model.layers.17.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "c7d7331485a2d5a52e2415034ac56a0c44e89ccf7a20a5b41a769181147ffdba.npy",
      "sha256": "aeefa6f6fda9f97e35b856e7fae4401fd627dc7cbe89dd046796195717f9616b",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.18.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "53b569f6a8c75e8ca7c16bcd6cd489da5812822c17b7376eb953ed71ebc98aa6.npy",
      "sha256": "d8dfc0585279221aa9cc1ec8b93177e83cd48675a9ec83ae5c9318100acff637",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.19.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "cfcb958acbc47f6a0c6ba6514bf424d4ebf1e65e05e99e266ce55601422aaa0d.npy",
      "sha256": "a635d1d157cd5245a90ee599f8ebbc2b3f4ef6c6dd0c68ae546296705476aee5",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.20.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "2d383293b38ed94a9ebe762db87adf6905c88e830ea656633fbb49c557cc77d6.npy",
      "sha256": "bf47f8bc46e5a655e179466938e978656c820d79f1059db78b2f19e0ef9164ff",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.21.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "3438a2fc73755d660a160c20895b0a6da0495946cae579b995cd40f5e928a9dc.npy",
      "sha256": "9e2436973b89336eedabc1a7f6dd9ebac9ea46f7d33cdddad0cec2bbfe846de4",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.22.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "6c141e33c8c72c1b73364682db8aafa901bf1243285958c5635cb193a6c2ae36.npy",
      "sha256": "e9c08a8ff0051325828e50ff20740edf96dadde2c0ea0875d4bf28a9ed5955ad",
      "shape": [
        128
      ]
    },
    "model.language_model.layers.23.self_attn.q_norm.weight": {
      "changed": 128,
      "dtype": "BF16",
      "file": "5c78ddbde110190e8894318b7ee805830f8c18f013b9719c1345f374eacf6619.npy",
      "sha256": "977bd2cb772248bf670534c54e1159c8a02f9dec46c2530e1d473de3c529b905",
      "shape": [
        128
      ]
    }
  }
}
```

**归档评价字段全文**

```json
{
  "candidate": "c-81dd85b39a266ffe7352e0792bf026051cb849eb066dc6276365d0bdd2b9c4d4",
  "full_development": true,
  "protocol": "3e8c0e3d36fe64c753c89f71bb3f9c2f6822455d3998e559ea9e80cbed7e2c52",
  "summary": {
    "accuracy": 0.6982758620689655,
    "cells": {
      "B0:T0:-:subset": {
        "correct": 31,
        "n": 58
      },
      "B0:T0:-:total": {
        "correct": 47,
        "n": 58
      },
      "B0:T1:-:subset": {
        "correct": 35,
        "n": 58
      },
      "B0:T1:-:total": {
        "correct": 47,
        "n": 58
      },
      "B1:T0:-:subset": {
        "correct": 34,
        "n": 58
      },
      "B1:T0:-:total": {
        "correct": 46,
        "n": 58
      },
      "B1:T1:-:subset": {
        "correct": 37,
        "n": 58
      },
      "B1:T1:-:total": {
        "correct": 47,
        "n": 58
      }
    },
    "format_errors": 0,
    "n": 464,
    "primary_groups": 58,
    "primary_joint": 0.5,
    "repair_score": 0.5258620689655172,
    "truncated": 0
  }
}
```

逐题数组保留在上述完整档案；本页未重新判分。数组身份/长度：`{"ids": 464, "predictions": 464, "scored": 464}`。

