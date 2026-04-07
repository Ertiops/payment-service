pytest_plugins = (
    "tests.plugins.factories.outbox",
    "tests.plugins.factories.payment",
    "tests.plugins.instances.config",
    "tests.plugins.instances.database.uow",
    "tests.plugins.instances.rest",
    "tests.plugins.instances.auth",
    "tests.plugins.use_cases.outbox",
    "tests.plugins.use_cases.payment",
    "tests.plugins.storages.database",
    "tests.plugins.instances.database.database",
)
