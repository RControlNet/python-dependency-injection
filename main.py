from cndi.annotations import Bean, Autowired, AppInitilizer

class TestBean:
    def __init__(self, name):
        self.name = name


@Bean()
def getTestBean() -> TestBean:
    return TestBean("Test 123")

testBean = None

@Autowired()
def setTestBean(bean: TestBean):
    global testBean
    testBean = bean

app = AppInitilizer()
if __name__ == "__main__":
    app.run()
    print(testBean.name)
    print(type(testBean))
