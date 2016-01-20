
default: compile

compile:
	pyinstaller -w -y main.spec
	cp -R dist/JupyterQt.app ./JupyterQt.app

clean:
	@echo "Cleaning build and dist folders"
	find . -iname "dist" -prune -exec rm -Rf {} \;
	find . -iname "build" -prune -exec rm -Rf {} \;

erase:
	find . -iname "JupyterQt.app" -prune -exec rm -Rf {} \;

run:
	open JupyterQt.app