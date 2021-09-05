from cndi.annotations import Bean
from test_module.TestBean import TestBean


@Bean()
def getTestBean() -> TestBean:
    return TestBean("Test 123")