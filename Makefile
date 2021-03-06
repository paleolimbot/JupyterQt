

osx: dist/JupyterQt.app/Contents/MacOS/main
dist/JupyterQt.app/Contents/MacOS/main : main.spec
	pyinstaller -w -y main.spec

runosx: osx
	open dist/JupyterQt.app

linux: dist/main/main
dist/main/main : main.spec
	pyinstaller -y main.spec

runlinux: linux
	dist/main/main

clean:
	@echo "Cleaning build and dist folders"
	find . -iname "dist" -prune -exec rm -Rf {} \;
	find . -iname "build" -prune -exec rm -Rf {} \;


