from cndi.annotations import Bean, Component
from cndi.initializers import AppInitializer
from test_module.TestBean import TestBean

@Bean()
def test() -> TestBean:
    return TestBean("Test Component")

@Component
class InjectBeanComponent:
    def __init__(self, testBean: TestBean):
        self.bean = testBean

        assert type(self.bean) is TestBean

app = AppInitializer()
app.run()