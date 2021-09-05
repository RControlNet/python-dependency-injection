from cndi.annotations import Bean, Autowired, AppInitilizer
from test_module.TestBean import TestBean

testBean = None

@Autowired()
def setTestBean(bean: TestBean):
    global testBean
    testBean = bean

app = AppInitilizer()
if __name__ == "__main__":
    app.componentScan("test_module")
    app.run()
    print(testBean.name)
    print(type(testBean))
