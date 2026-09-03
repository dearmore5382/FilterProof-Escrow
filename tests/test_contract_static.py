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
    assert methods == ["preview_proof", "create_job", "fund_job", "cancel_draft", "submit_proof", "assess_proof", "execute_release", "execute_refund", "recover_expired", "get_job", "get_attempt", "get_accounting", "get_counts"]


def test_preview_uses_real_core_without_storage_writes_or_transfers():
    preview = next(n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == "preview_proof")
    assert [ast.unparse(d) for d in preview.decorator_list] == ["gl.public.write"]
    code = ast.unparse(preview)
    assert "self._consensus_observation(" in code and "_derive_outcome(observation)" in code
    assert "PREVIEW_ONLY_NO_PAYMENT_AUTHORIZATION" in code
    assert "emit_transfer" not in code
    for node in ast.walk(preview):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            assert all(isinstance(target, ast.Name) for target in targets)


def test_real_custody_and_multimodal_consensus_are_present():
    assert "@gl.public.write.payable" in SOURCE
    assert "gl.message.value" in SOURCE
    assert "emit_transfer(value=amount)" in SOURCE
    vision_calls = [node for node in ast.walk(TREE) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name) and node.func.id == "_vision_result"]
    assert len(vision_calls) == 2
    assert [ast.literal_eval(node.args[1].elts[0].slice) for node in vision_calls] == [0, 1]
    assert [ast.literal_eval(node.args[1].elts[1].slice) for node in vision_calls] == [1, 2]
    assert all(len(node.args[1].elts) == 2 for node in vision_calls)
    assert "hashlib.sha256(body).hexdigest()" in SOURCE
    assert "run_nondet_unsafe" in SOURCE
    assert "_derive_outcome(theirs) == _derive_outcome(mine)" in SOURCE


def test_prompt_cannot_choose_money_flow():
    start = SOURCE.index('prompt = (')
    end = SOURCE.index('        overview = _vision_result', start)
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
