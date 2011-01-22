SRCDIR=src

SCRIPTS=${SRCDIR}/ganglia-logtailer

MODULES=`ls ${SRCDIR}/*.py`

all:
	@echo "======================= WAIT ========================"
	@echo "You need to supply a target. Available targets are"
	@echo "make (install|deb|source-deb|debclean)"	
	@echo "Files will be installed in ${DESTDIR}"
	@echo "To override type make DESTDIR=/opt install"
	@echo "====================================================="

install:
	install -d ${DESTDIR}/var/lib/ganglia-logtailer
	install -d ${DESTDIR}/var/log/ganglia-logtailer

	install -d ${DESTDIR}/usr/sbin
	install -m 0755 ${SCRIPTS} ${DESTDIR}/usr/sbin

	install -d ${DESTDIR}/usr/share/ganglia-logtailer
	install -m 0644 ${MODULES} ${DESTDIR}/usr/share/ganglia-logtailer

clean:
	-rm -f ganglia-logtailer.tar.gz

deb:
	debuild -uc -us -i -b

source-deb:
	debuild -uc -us -i -S

debclean:
	debuild clean

dist:
	hg archive -t tgz ganglia-logtailer.tar.gz

source-rpm: dist
	rpmbuild -ts ganglia-logtailer.tar.gz
	
rpm: dist 
	rpmbuild -tb ganglia-logtailer.tar.gz

