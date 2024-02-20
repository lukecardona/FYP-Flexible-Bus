from gymnasium.envs.registration import register

register(
    id="busHandlerEnv/busHandler-v0",
    entry_point="busHandlerEnv.envs:BusHandler",
    nondeterministic=True,
    order_enforce=True,
    kwargs={"numberOfBuses": 10, "numberOfRequests": 50}
)