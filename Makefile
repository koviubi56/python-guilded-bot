# SPDX-License-Identifier: GPL-3.0-or-later

PYTHON ?= "python3"                ## path to python executable (or just "python3")
REQUIREMENTS ?= "requirements.txt" ## path to the requirements.txt file
MAINFILE ?= "main.py"              ## path to the main.py file



help: ## show this help
	@sed -ne "s/^##\(.*\)/\1/p" $(MAKEFILE_LIST)
	@printf "────────────────────────`tput bold``tput setaf 2` Make Commands `tput sgr0`────────────────────────────────\n"
	@sed -ne "/@sed/!s/\(^[^#?=]*:\).*##\(.*\)/`tput setaf 2``tput bold`\1`tput sgr0`\2/p" $(MAKEFILE_LIST)
	@printf "────────────────────────`tput bold``tput setaf 4` Make Variables `tput sgr0`───────────────────────────────\n"
	@sed -ne "/@sed/!s/\(.*\)?=\(.*\)##\(.*\)/`tput setaf 4``tput bold`\1:`tput setaf 5`\2`tput sgr0`\3/p" $(MAKEFILE_LIST)
	@printf "───────────────────────────────────────────────────────────────────────\n"

# make help the default
.DEFAULT_GOAL := help

install_and_run: install run  ## Install the dependencies and run the bot

install:  ## Install the dependencies. IF PIP IS NOT FOUND RUN: sudo apt install python3-pip
	@$(PYTHON) -m pip install -U pip setuptools wheel
	@$(PYTHON) -m pip install -Ur $(REQUIREMENTS)

run:  ## Run the bot
	@$(PYTHON) $(MAINFILE)
