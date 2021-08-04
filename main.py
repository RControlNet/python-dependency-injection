from cndi.annotations import Bean, Autowired, AppInitilizer

class TestBean:
    def __init__(self, name):
        self.name = name


@Bean()
def getTestBean() -> TestBean:
    return TestBean("Test 123")

testBean = None

app = AppInitilizer()
if __name__ == "__main__":
    @Autowired()
    def setTestBean(bean: TestBean):
        global testBean
        testBean = bean

    app.run()

    print(testBean.name)
