"""CPU integration on a locally generated tiny random LLaMA, never experiment weights."""
import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


def run(output=None):
    import torch
    import transformers
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from transformers import GenerationConfig, LlamaConfig, LlamaForCausalLM, PreTrainedTokenizerFast
    from engine import CrossFamilyEngine, LAYERS, encode_text
    from preflight import checks

    started = time.monotonic()
    assert not torch.cuda.is_available()
    torch.manual_seed(20261026)
    vocabulary = {word: index for index, word in enumerate([
        "<unk>", "<bos>", "<eos>", "<|eot_id|>", "<|eom_id|>",
        "A", "library", "has", "three", "shelves", "with", "ten", "books", "each", ".",
        "Five", "are", "borrowed", "Answer", ":", "Twenty", "-", "five", "remain",
        "user", "assistant", "26", "Oct", "2026", "one", "two", "plus", "Question"])}
    backend = Tokenizer(WordLevel(vocabulary, unk_token="<unk>"))
    backend.pre_tokenizer = Whitespace()
    tokenizer = PreTrainedTokenizerFast(tokenizer_object=backend, bos_token="<bos>", eos_token="<eos>", unk_token="<unk>",
        additional_special_tokens=["<|eot_id|>", "<|eom_id|>"])
    tokenizer.chat_template = "{{ bos_token }}{{ date_string }} {% for m in messages %}{{ m['role'] }}: {{ m['content'] }} {% endfor %}{% if add_generation_prompt %}assistant: {% endif %}"
    config = LlamaConfig(vocab_size=len(vocabulary), hidden_size=32, intermediate_size=64,
        num_hidden_layers=16, num_attention_heads=4, num_key_value_heads=2,
        max_position_embeddings=256, bos_token_id=1, eos_token_id=2, pad_token_id=None,
        attention_dropout=0.0, tie_word_embeddings=False)
    random_model = LlamaForCausalLM(config).to(device="cpu", dtype=torch.bfloat16).eval()
    random_model.generation_config = GenerationConfig(bos_token_id=1, eos_token_id=[2, 3, 4], pad_token_id=None,
                                                     do_sample=False, use_cache=True)
    with TemporaryDirectory(prefix="acupuncture-cpu-random-llama-") as directory:
        model_dir = Path(directory) / "random-model"
        random_model.save_pretrained(model_dir)
        tokenizer.save_pretrained(model_dir)
        del random_model
        engine = CrossFamilyEngine(model_dir, device="cpu", batch_size=1, threads=2)
        assert all(parameter.device.type == "cpu" and parameter.dtype == torch.bfloat16 for parameter in engine.model.parameters())
        assert engine.stop_ids == [2, 3, 4] and engine.pad_id == 2
        assert encode_text(engine.tokenizer, "A library").count(1) == 1
        rendered = engine.tokenizer.apply_chat_template([{"role": "user", "content": "A library"}],
            tokenize=False, add_generation_prompt=True)
        assert "26 Oct 2026" in rendered and encode_text(engine.tokenizer, rendered).count(1) == 1
        vector = torch.zeros(config.hidden_size)
        vector[0] = 1.0
        engine.conditions["true_D_match"] = {str(layer): {"kind": "vector", "vector": vector.clone(),
            "scale": "target", "coefficient": 1.0} for layer in LAYERS}
        engine.conditions["true_S_recipe"] = {str(layer): {"kind": "channel", "index": 5,
            "scale": "target", "coefficient": 1.0 / float(engine.column_norms[str(layer)][5])} for layer in LAYERS}
        results = {str(stage): checks(engine, stage) for stage in (1, 2)}
        assert all(result["zero_and_restoration_exact"] and result["real_arm_changed_logits"] for result in results.values())
        assert all(value > 0 for result in results.values() for row in result["calibration"] for value in row["residual_scales"].values())
        prompt = "A library has three shelves. Answer:"
        calibration = engine.calibrate([prompt])
        ids = encode_text(engine.tokenizer, prompt)
        inputs = engine._inputs([ids])
        try:
            with engine._intervention("true_S_recipe", calibration, inputs["attention_mask"]):
                raise RuntimeError("intentional hook cleanup test")
        except RuntimeError as error:
            assert str(error) == "intentional hook cleanup test"
        unchanged = engine.verify_unchanged()
        result = {"status": "completed", "scientific_experiment": False,
            "model": "random-initialized CPU LlamaForCausalLM; 16 layers, hidden32, intermediate64",
            "downloaded_weights": False, "loaded_experiment_model": False, "gpu_available": torch.cuda.is_available(),
            "versions": {"torch": str(torch.__version__), "transformers": str(transformers.__version__)},
            "checks": results, "exception_cleanup": True, **unchanged, "elapsed_seconds": time.monotonic() - started}
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as handle:
            handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "checks"}, ensure_ascii=False))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    run(parser.parse_args().output)
