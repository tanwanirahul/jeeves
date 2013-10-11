'''
This tests code after the macro transformation.

Before the transformation, there would be calls to mkLabel and restrict but
the jifs should be gone. It would also 
'''
#import macropy.activate
from smt.Z3 import *
import unittest
import JeevesGlobal
import JeevesLib
from env.PathVars import PositiveVariable, NegativeVariable

class TestJeevesConfidentiality(unittest.TestCase):
  def setUp(self):
    self.s = Z3()
    # reset the Jeeves state
    JeevesGlobal.set_jeeves_state(JeevesLib.JeevesLib())

  def test_restrict_all_permissive(self):
    x = JeevesGlobal.jeevesLib.mkLabel('x')
    JeevesGlobal.jeevesLib.restrict(x, lambda _: True)
    xConcrete = JeevesGlobal.jeevesLib.concretize(None, x)
    # make sure that concretizing x allows everyone to see
    self.assertTrue(xConcrete)

  def test_restrict_all_restrictive(self):
    x = JeevesGlobal.jeevesLib.mkLabel('x')
    JeevesGlobal.jeevesLib.restrict(x, lambda _: False)
    xConcrete = JeevesGlobal.jeevesLib.concretize(None, x)
    self.assertFalse(xConcrete)

  def test_restrict_with_context(self):
    x = JeevesGlobal.jeevesLib.mkLabel('x')
    JeevesGlobal.jeevesLib.restrict(x, lambda y: y == 2)

    xConcrete = JeevesGlobal.jeevesLib.concretize(2, x)
    self.assertTrue(xConcrete)

    xConcrete = JeevesGlobal.jeevesLib.concretize(3, x)
    self.assertFalse(xConcrete)

  def test_restrict_with_sensitivevalue(self):
    x = JeevesGlobal.jeevesLib.mkLabel('x')
    JeevesGlobal.jeevesLib.restrict(x, lambda y: y == 2)
    value = JeevesGlobal.jeevesLib.mkSensitive(x, 42, 41)

    valueConcrete = JeevesGlobal.jeevesLib.concretize(2, value)
    self.assertEquals(valueConcrete, 42)

    valueConcrete = JeevesGlobal.jeevesLib.concretize(1, value)
    self.assertEquals(valueConcrete, 41)

  def test_restrict_with_cyclic(self):
    jl = JeevesGlobal.jeevesLib

    # use the value itself as the context
    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt == 42)

    value = jl.mkSensitive(x, 42, 20)
    self.assertEquals(jl.concretize(value, value), 42)

    value = jl.mkSensitive(x, 41, 20)
    self.assertEquals(jl.concretize(value, value), 20)

  def test_jif_with_ints(self):
    jl = JeevesGlobal.jeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt == 42)

    a = jl.jif(x, lambda:13, lambda:17 )
    self.assertEquals(jl.concretize(42, a), 13)
    self.assertEquals(jl.concretize(-2, a), 17)

    b = jl.jif(True, lambda:13, lambda:17)
    self.assertEquals(jl.concretize(42, b), 13)
    self.assertEquals(jl.concretize(-2, b), 13)

    c = jl.jif(False, lambda:13, lambda:17)
    self.assertEquals(jl.concretize(42, c), 17)
    self.assertEquals(jl.concretize(-2, c), 17)

    conditional = jl.mkSensitive(x, True, False)
    d = jl.jif(conditional, lambda:13, lambda:17)
    self.assertEquals(jl.concretize(42, d), 13)
    self.assertEquals(jl.concretize(-2, d), 17)

    conditional = jl.mkSensitive(x, False, True)
    d = jl.jif(conditional, lambda:13, lambda:17)
    self.assertEquals(jl.concretize(42, d), 17)
    self.assertEquals(jl.concretize(-2, d), 13)

    y = jl.mkLabel('y')
    z = jl.mkLabel('z')
    jl.restrict(y, lambda (a,_) : a)
    jl.restrict(z, lambda (_,a) : a)
    faceted_int = jl.mkSensitive(y, 10, 0)
    conditional = faceted_int > 5
    i1 = jl.mkSensitive(z, 101, 102)
    i2 = jl.mkSensitive(z, 103, 104)
    f = jl.jif(conditional, lambda:i1, lambda:i2)
    self.assertEquals(jl.concretize((True, True), f),101)
    self.assertEquals(jl.concretize((True, False), f), 102)
    self.assertEquals(jl.concretize((False, True), f), 103)
    self.assertEquals(jl.concretize((False, False), f), 104)

  def test_jif_with_objects(self):
    return NotImplemented

  def test_restrict_under_conditional(self):
    jl = JeevesGlobal.jeevesLib

    x = jl.mkLabel('x')
    def yes_restrict():
        jl.restrict(x, lambda ctxt : ctxt == 1)
    def no_restrict():
        pass

    value = jl.mkSensitive(x, 42, 0)
    jl.jif(value == 42, yes_restrict, no_restrict)
    self.assertEquals(jl.concretize(0, value), 0)
    self.assertEquals(jl.concretize(1, value), 42)

    y = jl.mkLabel('y')
    def yes_restrict():
        jl.restrict(y, lambda ctxt : ctxt == 1)
    def no_restrict():
        pass

    value = jl.mkSensitive(y, 43, 0)
    jl.jif(value == 42, yes_restrict, no_restrict)
    self.assertEquals(jl.concretize(0, value), 43)
    self.assertEquals(jl.concretize(1, value), 43)

  def test_jbool_functions_constants(self):
    jl = JeevesGlobal.jeevesLib

    self.assertEquals(jl.jand(lambda:True, lambda:True), True)
    self.assertEquals(jl.jand(lambda:True, lambda:False), False)
    self.assertEquals(jl.jand(lambda:False, lambda:True), False)
    self.assertEquals(jl.jand(lambda:False, lambda:False), False)

    self.assertEquals(jl.jor(lambda:True, lambda:True), True)
    self.assertEquals(jl.jor(lambda:True, lambda:False), True)
    self.assertEquals(jl.jor(lambda:False, lambda:True), True)
    self.assertEquals(jl.jor(lambda:False, lambda:False), False)

    self.assertEquals(jl.jnot(True), False)
    self.assertEquals(jl.jnot(False), True)

  def test_jbool_functions_fexprs(self):
    jl = JeevesGlobal.jeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda (a,_) : a == 42)

    for lh in (True, False):
      for ll in (True, False):
        for rh in (True, False):
          for rl in (True, False):
            l = jl.mkSensitive(x, lh, ll)
            r = jl.mkSensitive(x, rh, rl)
            self.assertEquals(jl.concretize((42,0), jl.jand(lambda:l, lambda:r)), lh and rh)
            self.assertEquals(jl.concretize((10,0), jl.jand(lambda:l, lambda:r)), ll and rl)
            self.assertEquals(jl.concretize((42,0), jl.jor(lambda:l, lambda:r)), lh or rh)
            self.assertEquals(jl.concretize((10,0), jl.jor(lambda:l, lambda:r)), ll or rl)
            self.assertEquals(jl.concretize((42,0), jl.jnot(l)), not lh)
            self.assertEquals(jl.concretize((10,0), jl.jnot(l)), not ll)

    y = jl.mkLabel('y')
    jl.restrict(y, lambda (_,b) : b == 42)

    for lh in (True, False):
      for ll in (True, False):
        for rh in (True, False):
          for rl in (True, False):
            l = jl.mkSensitive(x, lh, ll)
            r = jl.mkSensitive(y, rh, rl)
            self.assertEquals(jl.concretize((42,0), jl.jand(lambda:l, lambda:r)), lh and rl)
            self.assertEquals(jl.concretize((10,0), jl.jand(lambda:l, lambda:r)), ll and rl)
            self.assertEquals(jl.concretize((42,42), jl.jand(lambda:l, lambda:r)), lh and rh)
            self.assertEquals(jl.concretize((10,42), jl.jand(lambda:l, lambda:r)), ll and rh)

            self.assertEquals(jl.concretize((42,0), jl.jor(lambda:l, lambda:r)), lh or rl)
            self.assertEquals(jl.concretize((10,0), jl.jor(lambda:l, lambda:r)), ll or rl)
            self.assertEquals(jl.concretize((42,42), jl.jor(lambda:l, lambda:r)), lh or rh)
            self.assertEquals(jl.concretize((10,42), jl.jor(lambda:l, lambda:r)), ll or rh)

  def test_nested_conditionals_no_shared_path(self):
    return NotImplemented

  def test_nested_conditionals_shared_path(self):
    return NotImplemented

  def test_jif_with_assign(self):
    jl = JeevesGlobal.jeevesLib

    y = jl.mkLabel('y')
    jl.restrict(y, lambda ctxt : ctxt == 42)

    value0 = jl.mkSensitive(y, 0, 1)
    value2 = jl.mkSensitive(y, 2, 3)

    value = value0
    value = jl.jassign(value, value2)
    self.assertEquals(jl.concretize(42, value), 2)
    self.assertEquals(jl.concretize(10, value), 3)

    value = 100
    value = jl.jassign(value, value2)
    self.assertEquals(jl.concretize(42, value), 2)
    self.assertEquals(jl.concretize(10, value), 3)

    value = value0
    value = jl.jassign(value, 200)
    self.assertEquals(jl.concretize(42, value), 200)
    self.assertEquals(jl.concretize(10, value), 200)

    value = 100
    value = jl.jassign(value, 200)
    self.assertEquals(jl.concretize(42, value), 200)
    self.assertEquals(jl.concretize(10, value), 200)

  def test_jif_with_assign_with_pathvars(self):
    jl = JeevesGlobal.jeevesLib

    x = jl.mkLabel('x')
    y = jl.mkLabel('y')
    jl.restrict(x, lambda (a,_) : a)
    jl.restrict(y, lambda (_,b) : b)

    value0 = jl.mkSensitive(y, 0, 1)
    value2 = jl.mkSensitive(y, 2, 3)

    value = value0
    with PositiveVariable(x):
      value = jl.jassign(value, value2)
    self.assertEquals(jl.concretize((True, True), value), 2)
    self.assertEquals(jl.concretize((True, False), value), 3)
    self.assertEquals(jl.concretize((False, True), value), 0)
    self.assertEquals(jl.concretize((False, False), value), 1)

    value = value0
    with NegativeVariable(x):
      value = jl.jassign(value, value2)
    self.assertEquals(jl.concretize((False, True), value), 2)
    self.assertEquals(jl.concretize((False, False), value), 3)
    self.assertEquals(jl.concretize((True, True), value), 0)
    self.assertEquals(jl.concretize((True, False), value), 1)

  def test_function_facets(self):
    def add1(a):
        return a+1
    def add2(a):
        return a+2

    jl = JeevesGlobal.jeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt == 42)

    fun = jl.mkSensitive(x, add1, add2)
    value = fun(15)
    self.assertEquals(jl.concretize(42, value), 16)
    self.assertEquals(jl.concretize(41, value), 17)

  def test_objects_faceted(self):
    class TestClass:
      def __init__(self, a, b):
        self.a = a
        self.b = b

    jl = JeevesGlobal.jeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt)

    y = jl.mkSensitive(x,
      TestClass(1, 2),
      TestClass(3, 4))

    self.assertEquals(jl.concretize(True, y.a), 1)
    self.assertEquals(jl.concretize(True, y.b), 2)
    self.assertEquals(jl.concretize(False, y.a), 3)
    self.assertEquals(jl.concretize(False, y.b), 4)

  def test_objects_mutate(self):
    class TestClass:
      def __init__(self, a, b):
        self.a = a
        self.b = b

    jl = JeevesGlobal.jeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt)

    s = TestClass(1, None)
    t = TestClass(3, None)
    y = jl.mkSensitive(x, s, t)

    def mut():
      y.a = jl.jassign(y.a, y.a + 100)
    def nonmut():
      pass

    jl.jif(y.a == 1, mut, nonmut)

    self.assertEquals(jl.concretize(True, y.a), 101)
    self.assertEquals(jl.concretize(True, s.a), 101)
    self.assertEquals(jl.concretize(True, t.a), 3)
    self.assertEquals(jl.concretize(False, y.a), 3)
    self.assertEquals(jl.concretize(False, s.a), 1)
    self.assertEquals(jl.concretize(False, t.a), 3)

  def test_objects_methodcall(self):
    class TestClassMethod:
      def __init__(self, a, b):
        self.a = a
        self.b = b
      def add_a_to_b(self):
        self.b = JeevesGlobal.jeevesLib.jassign(self.b, self.a + self.b)
      def return_sum(self):
        return self.a + self.b

    jl = JeevesGlobal.jeevesLib

    x = jl.mkLabel('x')
    jl.restrict(x, lambda ctxt : ctxt)

    s = TestClassMethod(1, 10)
    t = TestClassMethod(100, 1000)
    y = jl.mkSensitive(x, s, t)

    self.assertEquals(jl.concretize(True, y.return_sum()), 11)
    self.assertEquals(jl.concretize(False, y.return_sum()), 1100)

    y.add_a_to_b()
    self.assertEquals(jl.concretize(True, s.a), 1)
    self.assertEquals(jl.concretize(True, s.b), 11)
    self.assertEquals(jl.concretize(True, t.a), 100)
    self.assertEquals(jl.concretize(True, t.b), 1000)
    self.assertEquals(jl.concretize(True, y.a), 1)
    self.assertEquals(jl.concretize(True, y.b), 11)
    self.assertEquals(jl.concretize(False, s.a), 1)
    self.assertEquals(jl.concretize(False, s.b), 10)
    self.assertEquals(jl.concretize(False, t.a), 100)
    self.assertEquals(jl.concretize(False, t.b), 1100)
    self.assertEquals(jl.concretize(False, y.a), 100)
    self.assertEquals(jl.concretize(False, y.b), 1100)

  def test_objects_eq_is(self):
    class TestClassEq:
      def __init__(self, a, b):
        self.a = a
        self.b = b
      def __eq__(self, other):
        return self.a == other.a and self.b == other.b

    return NotImplemented

  def test_objects_operators(self):
    return NotImplemented

  def test_objects_delattr(self):
    return NotImplemented

if __name__ == '__main__':
    unittest.main()
