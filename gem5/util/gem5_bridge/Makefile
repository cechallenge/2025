DRIVER := gem5_bridge
GROUP  := gem5

ifneq ($(KERNELRELEASE),)
obj-m += $(DRIVER).o

else
PWD         ?= $(shell pwd)
KVERSION    ?= $(shell uname -r)
KMAKEDIR    ?= /lib/modules/$(KVERSION)/build
MODLOADCONF ?= /etc/modules-load.d/$(GROUP).conf

.PHONY: build
build:
	make -C $(KMAKEDIR) M=$(PWD) modules

.PHONY: install
install:
	make -C $(KMAKEDIR) M=$(PWD) INSTALL_MOD_DIR=$(GROUP) modules_install
	# May need to manually run `depmod --quick` before running `modprobe`

.PHONY: clean
clean:
	make -C $(KMAKEDIR) M=$(PWD) clean

endif
