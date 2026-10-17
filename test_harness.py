import importlib.util
import pickle
import sys
import types
from pathlib import Path


class Map(dict):
    @classmethod
    def __class_getitem__(cls, _):
        return cls


class Return:
    def __init__(self, value): self.calldata = value


class UserError(Exception): pass


class Response:
    def __init__(self, body): self.body = body.encode()


def load():
    prompts, bodies = [], []
    def prompt(_): return prompts.pop(0)
    def get(_): return Response(bodies.pop(0))
    def run(action, validator):
        value = action(); assert pickle.loads(pickle.dumps(value)) == value
        if not validator(Return(value)): raise UserError("disagreement")
        return value
    identity = lambda fn: fn
    gl = types.SimpleNamespace(Contract=object, public=types.SimpleNamespace(write=identity, view=identity),
        message=types.SimpleNamespace(sender_address="0xowner"),
        vm=types.SimpleNamespace(Return=Return, UserError=UserError, run_nondet_unsafe=run),
        nondet=types.SimpleNamespace(exec_prompt=prompt, web=types.SimpleNamespace(get=get)))
    module = types.ModuleType("genlayer"); module.gl = gl; module.TreeMap = Map; module.__all__ = ["gl", "TreeMap"]
    sys.modules["genlayer"] = module
    spec = importlib.util.spec_from_file_location("intent_router", Path(__file__).with_name("intent_router.py"))
    loaded = importlib.util.module_from_spec(spec); spec.loader.exec_module(loaded)
    contract = loaded.IntentRouter.__new__(loaded.IntentRouter); contract.intents = Map(); contract.__init__()
    return contract, prompts, bodies, UserError
