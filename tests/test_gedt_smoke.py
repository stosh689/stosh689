import importlib


def test_core_modules_import():
    modules = [
        "cidar",
        "ml_model",
        "realtime",
        "resource_optimization",
    ]

    for module_name in modules:
        module = importlib.import_module(module_name)
        assert module is not None