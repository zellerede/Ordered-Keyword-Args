import sys
sys.path.insert(1, '../Src')

if 'orderedkwargs' in sys.modules:
    reload(sys.modules['orderedkwargs'])
from orderedkwargs import orderedkwargs

@orderedkwargs
def define_record(record_name, kwargs) :
    print "record: %s" % (record_name,)
    print "fields: %s" % (kwargs.items(),)
    print

define_record("Point", x="Int32", y="Int32")
define_record("Person", name="Text", salary="Number")
define_record(z="Int32",  y="Int32", record_name="zy_x", x="Int32")

# test within a class
class A:
    @orderedkwargs
    def func(self, name, kwargs):
        print self, name
        print kwargs
        print

    @orderedkwargs
    def func_with_args(self, name, kwargs, *args):
        print self, name, args
        print kwargs
        print

    @orderedkwargs  # now should do nothing
    def __repr__(self):
        return "an A object"

a=A()
a.func('Rufus', height=174, weight=82)
a.func_with_args('Sam', params='A7', setup='Idle')
a.func_with_args('John', 1, 2, 3, 4, cash='much', girls='many')


# test with other name
@orderedkwargs('fields')
def medal(kwargs, fields):
    print kwargs
    print fields.items()
    print

medal(42, x=1, y=2, z=3)

@orderedkwargs('fields')
def define_record(record_name, fields, *args) :
    print "record: %s" % (record_name,)
    print "fields: %s" % (fields.items(),)
    if args:
        print "additional arguments:", args

define_record("Point", 1, 2, 3, 4,  x="Int32", y="Int32")
