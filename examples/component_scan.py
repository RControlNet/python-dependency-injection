from cndi.initializers import AppInitializer

app_initializer = AppInitializer()
app_initializer.componentScan("test_components")
app_initializer.run()