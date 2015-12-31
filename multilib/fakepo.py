class FakePackageObject(object):
    """
    fake package object that contains enough data to run through the testing
    framework herein
    """
    def __init__(self, po=None, d=None):
        # FPO's can be created from yum Package Objects or dictionaries
        if po:
            self.name = po.name
            self.arch = po.arch
            self.provides = po.provides
            self.files = po.returnFileEntries()
        elif d:
            self.name = d['name']
            self.arch = d['arch']
            self.provides = d['provides']
            self.files = d['files']
        else:
            raise RuntimeError('fake package objects must come from a real yum object or dictionary')

    def convert(self):
        return {
            'name': self.name,
            'arch': self.arch,
            'provides': self.provides,
            'files': self.files
        }

    def returnFileEntries(self):
        return self.files

