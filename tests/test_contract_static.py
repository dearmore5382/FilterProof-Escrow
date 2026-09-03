import ast
from pathlib import Path


CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "FilterProofEscrow.py"
SOURCE = CONTRACT.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def test_public_surface_and_types():
    methods = []
    for node in ast.walk(TREE):
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            decorators = {ast.unparse(item) for item in node.decorator_list}
            if decorators & {"gl.public.write", "gl.public.write.payable", "gl.public.view"}:
                methods.append(node.name)
                assert decorators <= {"gl.public.write", "gl.public.write.payable", "gl.public.view"}
                assert node.returns is not None
                assert all(arg.annotation is not None for arg in node.args.args[1:])
    assert methods == ["create_job", "fund_job", "cancel_draft", "submit_proof", "assess_proof", "execute_release", "execute_refund", "recover_expired", "get_job", "get_attempt", "get_accounting", "get_counts"]


def test_real_custody_and_multimodal_consensus_are_present():
    assert "@gl.public.write.payable" in SOURCE
    assert "gl.message.value" in SOURCE
    assert "emit_transfer(value=amount)" in SOURCE
    assert "MAX_VISION_IMAGES = 2" in SOURCE
    assert "images=images[:MAX_VISION_IMAGES]" in SOURCE
    assert "response_format=" not in SOURCE
    assert "hashlib.sha256(body).hexdigest()" in SOURCE
    assert "run_nondet_unsafe" in SOURCE
    assert "_derive_outcome(theirs) == _derive_outcome(mine)" in SOURCE


def test_prompt_cannot_choose_money_flow():
    start = SOURCE.index('prompt = (')
    end = SOURCE.index('        raw = gl.nondet.exec_prompt', start)
    prompt = SOURCE[start:end]
    assert "Do not return verdict, payment, refund, beneficiary" in prompt
    assert "RELEASE_AUTHORIZED" not in prompt
    assert "REFUND_AUTHORIZED" not in prompt


def test_no_constructor_arguments_and_bounded_fetches():
    cls = next(node for node in TREE.body if isinstance(node, ast.ClassDef) and node.name == "FilterProofEscrow")
    init = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
    assert len(init.args.args) == 1
    assert "MAX_MANIFEST_BYTES" in SOURCE and "MAX_IMAGE_BYTES" in SOURCE
    assert SOURCE.count("gl.nondet.web.get") == 2
