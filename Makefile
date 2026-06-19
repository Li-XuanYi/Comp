.PHONY: check test node00 node01 node02 node03 node04 node05 node06 node07 node08 node09 node10 node11 node12

test:
	pytest -q

check:
	python scripts/check_node.py --node all
	pytest -q

node00:
	python scripts/run_node.py --node node00
	python scripts/check_node.py --node node00

node01:
	python scripts/run_node.py --node node01
	python scripts/check_node.py --node node01

node02:
	python scripts/run_node.py --node node02
	python scripts/check_node.py --node node02

node03:
	python scripts/run_node.py --node node03
	python scripts/check_node.py --node node03

node04:
	python scripts/run_node.py --node node04
	python scripts/check_node.py --node node04

node05:
	python scripts/run_node.py --node node05
	python scripts/check_node.py --node node05

node06:
	python scripts/run_node.py --node node06
	python scripts/check_node.py --node node06

node07:
	python scripts/run_node.py --node node07
	python scripts/check_node.py --node node07

node08:
	python scripts/run_node.py --node node08
	python scripts/check_node.py --node node08

node09:
	python scripts/run_node.py --node node09
	python scripts/check_node.py --node node09

node10:
	python scripts/run_node.py --node node10
	python scripts/check_node.py --node node10

node11:
	python scripts/run_node.py --node node11
	python scripts/check_node.py --node node11

node12:
	python scripts/make_all_outputs.py
	python scripts/check_node.py --node node12

