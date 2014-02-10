from django.db import models
from django.utils import unittest
from django.test import TestCase

import JeevesLib

from jeevesdb import JeevesModel
from testdb.models import Animal

def parse_vars_row(vs):
  d = {}
  for entry in vs.split(';')[1:-1]:
    name, val = entry.split('=')
    d[name] = bool(int(val))
  return d

# expected is a list
# [({name:'lion',...}, {var_name:True,...})]
def areRowsEqual(rows, expected):
  rows = list(rows)
  if len(rows) != len(expected):
    print 'got len %d, expected %d' % (len(rows), len(expected))
    return False
  for attrs_dict, vars_dict in expected:
    for r in rows:
      vars_dict1 = parse_vars_row(r.jeeves_vars)
      if (vars_dict == vars_dict1 and
          all(getattr(r, name) == val for name, val in attrs_dict.iteritems())):
          break
    else:
      print 'could not find', attrs_dict, vars_dict
      return False
  return True

class TestJeevesModel(TestCase):
  def setUp(self):
    JeevesLib.init()

    Animal.objects.create(name='lion', sound='roar')
    Animal.objects.create(name='cat', sound='meow')

    self.x = JeevesLib.mkLabel()
    self.y = JeevesLib.mkLabel()
    JeevesLib.restrict(self.x, lambda (a,_) : a)
    JeevesLib.restrict(self.y, lambda (_,a) : a)

    Animal.objects.create(name='fox',
        sound=JeevesLib.mkSensitive(self.x, 'Hatee-hatee-hatee-ho!',
            'Joff-tchoff-tchoff-tchoffo-tchoffo-tchoff!'))

    Animal.objects.create(name='a',
        sound=JeevesLib.mkSensitive(self.x,
            JeevesLib.mkSensitive(self.y, 'b', 'c'),
            JeevesLib.mkSensitive(self.y, 'd', 'e')))

  def testWrite(self):
    lion = Animal._objects_ordinary.get(name='lion')
    self.assertEquals(lion.name, 'lion')
    self.assertEquals(lion.sound, 'roar')
    self.assertEquals(lion.jeeves_vars, ';')

    fox = Animal._objects_ordinary.filter(name='fox').filter(jeeves_vars=';%s=1;'%self.x.name).all()[0]
    self.assertEquals(fox.sound, 'Hatee-hatee-hatee-ho!')
    fox = Animal._objects_ordinary.filter(name='fox').filter(jeeves_vars=';%s=0;'%self.x.name).all()[0]
    self.assertEquals(fox.sound, 'Joff-tchoff-tchoff-tchoffo-tchoffo-tchoff!')

    a = list(Animal._objects_ordinary.filter(name='a').all())
    self.assertTrue(areRowsEqual(a, [
      ({'name':'a', 'sound':'b'}, {self.x.name:True, self.y.name:True}),
      ({'name':'a', 'sound':'c'}, {self.x.name:True, self.y.name:False}),
      ({'name':'a', 'sound':'d'}, {self.x.name:False, self.y.name:True}),
      ({'name':'a', 'sound':'e'}, {self.x.name:False, self.y.name:False}),
     ]))

  def testQueryDelete(self):
    Animal.objects.create(name='delete_test1',
        sound=JeevesLib.mkSensitive(self.x,
            JeevesLib.mkSensitive(self.y, 'b', 'c'),
            JeevesLib.mkSensitive(self.y, 'd', 'e')))
    Animal.objects.filter(name='delete_test1').filter(sound='b').delete()
    a = list(Animal._objects_ordinary.filter(name='delete_test1').all())
    self.assertTrue(areRowsEqual(a, [
      ({'name':'delete_test1', 'sound':'c'}, {self.x.name:True, self.y.name:False}),
      ({'name':'delete_test1', 'sound':'d'}, {self.x.name:False, self.y.name:True}),
      ({'name':'delete_test1', 'sound':'e'}, {self.x.name:False, self.y.name:False}),
     ]))

    an = Animal.objects.create(name='delete_test2',
        sound=JeevesLib.mkSensitive(self.x,
            JeevesLib.mkSensitive(self.y, 'b', 'c'),
            JeevesLib.mkSensitive(self.y, 'd', 'e')))
    with JeevesLib.PositiveVariable(self.x):
      an.delete()
    a = list(Animal._objects_ordinary.filter(name='delete_test2').all())
    self.assertTrue(areRowsEqual(a, [
      ({'name':'delete_test2', 'sound':'d'}, {self.x.name:False, self.y.name:True}),
      ({'name':'delete_test2', 'sound':'e'}, {self.x.name:False, self.y.name:False}),
     ]))

    an = Animal.objects.create(name='delete_test3', sound='b')
    with JeevesLib.PositiveVariable(self.x):
      an.delete()
    a = list(Animal._objects_ordinary.filter(name='delete_test3').all())
    self.assertTrue(areRowsEqual(a, [
      ({'name':'delete_test3', 'sound':'b'}, {self.x.name:False})
    ]))

    an = Animal.objects.create(name='delete_test4', sound='b')
    with JeevesLib.PositiveVariable(self.x):
      with JeevesLib.NegativeVariable(self.y):
        an.delete()
    a = list(Animal._objects_ordinary.filter(name='delete_test4').all())
    self.assertTrue(areRowsEqual(a, [
      ({'name':'delete_test4', 'sound':'b'}, {self.x.name:False}),
      ({'name':'delete_test4', 'sound':'b'}, {self.x.name:True, self.y.name:True}),
    ]) or areRowsEqual(a, [
      ({'name':'delete_test4', 'sound':'b'}, {self.y.name:True}),
      ({'name':'delete_test4', 'sound':'b'}, {self.y.name:False, self.x.name:False}),
    ]))

    an = Animal.objects.create(name='delete_test5',
            sound=JeevesLib.mkSensitive(self.x, 'b', 'c'))
    with JeevesLib.PositiveVariable(self.x):
      an.delete()
    a = list(Animal._objects_ordinary.filter(name='delete_test5').all())
    self.assertTrue(areRowsEqual(a, [
      ({'name':'delete_test5', 'sound':'c'}, {self.x.name:False})
    ]))

    an = Animal.objects.create(name='delete_test6',
            sound=JeevesLib.mkSensitive(self.x, 'b', 'c'))
    with JeevesLib.PositiveVariable(self.y):
      an.delete()
    a = list(Animal._objects_ordinary.filter(name='delete_test6').all())
    self.assertTrue(areRowsEqual(a, [
      ({'name':'delete_test6', 'sound':'b'}, {self.x.name:True,self.y.name:False}),
      ({'name':'delete_test6', 'sound':'c'}, {self.x.name:False,self.y.name:False}),
    ]))

  def testSave(self):
    an = Animal.objects.create(name='save_test1', sound='b')
    an.sound = 'c'
    with JeevesLib.PositiveVariable(self.x):
      an.save()
    a = list(Animal._objects_ordinary.filter(name='save_test1').all())
    self.assertTrue(areRowsEqual(a, [
      ({'name':'save_test1', 'sound':'b'}, {self.x.name:False}),
      ({'name':'save_test1', 'sound':'c'}, {self.x.name:True}),
    ]))

    an = Animal.objects.create(name='save_test2', sound='b')
    an.sound = 'c'
    with JeevesLib.PositiveVariable(self.x):
      with JeevesLib.NegativeVariable(self.y):
        an.save()
    a = list(Animal._objects_ordinary.filter(name='save_test2').all())
    self.assertTrue(areRowsEqual(a, [
      ({'name':'save_test2', 'sound':'c'}, {self.x.name:True, self.y.name:False}),
      ({'name':'save_test2', 'sound':'b'}, {self.x.name:True, self.y.name:True}),
      ({'name':'save_test2', 'sound':'b'}, {self.x.name:False}),
    ]) or areRowsEqual(a, [
      ({'name':'save_test2', 'sound':'c'}, {self.x.name:True, self.y.name:False}),
      ({'name':'save_test2', 'sound':'b'}, {self.x.name:False, self.y.name:False}),
      ({'name':'save_test2', 'sound':'b'}, {self.y.name:True}),
    ]))

    an = Animal.objects.create(name='save_test3',
        sound=JeevesLib.mkSensitive(self.x, 'b', 'c'))
    an.sound = JeevesLib.mkSensitive(self.x, 'd', 'e')
    an.save()
    a = list(Animal._objects_ordinary.filter(name='save_test3').all())
    self.assertTrue(areRowsEqual(a, [
      ({'name':'save_test3', 'sound':'d'}, {self.x.name:True}),
      ({'name':'save_test3', 'sound':'e'}, {self.x.name:False}),
    ]))

    an = Animal.objects.create(name='save_test4',
        sound=JeevesLib.mkSensitive(self.x, 'b', 'c'))
    an.sound = JeevesLib.mkSensitive(self.y, 'd', 'e')
    an.save()
    a = list(Animal._objects_ordinary.filter(name='save_test4').all())
    self.assertTrue(areRowsEqual(a, [
        ({'name':'save_test4', 'sound':'d'}, {self.y.name:True}),
        ({'name':'save_test4', 'sound':'e'}, {self.y.name:False}),
    ]) or areRowsEqual(a, [
        ({'name':'save_test4', 'sound':'d'}, {self.y.name:True, self.x.name:True}),
        ({'name':'save_test4', 'sound':'d'}, {self.y.name:True, self.x.name:False}),
        ({'name':'save_test4', 'sound':'e'}, {self.y.name:False, self.x.name:True}),
        ({'name':'save_test4', 'sound':'e'}, {self.y.name:False, self.x.name:False}),
    ]))

    an = Animal.objects.create(name='save_test5',
        sound=JeevesLib.mkSensitive(self.x, 'b', 'c'))
    an.sound = JeevesLib.mkSensitive(self.y, 'd', 'e')
    with JeevesLib.PositiveVariable(self.x):
      an.save()
    a = list(Animal._objects_ordinary.filter(name='save_test5').all())
    self.assertTrue(areRowsEqual(a, [
        ({'name':'save_test5', 'sound':'c'}, {self.x.name:False}),
        ({'name':'save_test5', 'sound':'d'}, {self.x.name:True, self.y.name:True}),
        ({'name':'save_test5', 'sound':'e'}, {self.x.name:True, self.y.name:False}),
    ]))

    an = Animal.objects.create(name='save_test6',
        sound=JeevesLib.mkSensitive(self.x, 'b', 'c'))
    an.sound = JeevesLib.mkSensitive(self.y, 'd', 'e')
    with JeevesLib.PositiveVariable(self.y):
      an.save()
    a = list(Animal._objects_ordinary.filter(name='save_test6').all())
    self.assertTrue(areRowsEqual(a, [
        ({'name':'save_test6', 'sound':'b'}, {self.x.name:True, self.y.name:False}),
        ({'name':'save_test6', 'sound':'d'}, {self.x.name:True, self.y.name:True}),
        ({'name':'save_test6', 'sound':'c'}, {self.x.name:False, self.y.name:False}),
        ({'name':'save_test6', 'sound':'d'}, {self.x.name:False, self.y.name:True}),
    ]) or areRowsEqual(a, [
        ({'name':'save_test6', 'sound':'b'}, {self.x.name:True, self.y.name:False}),
        ({'name':'save_test6', 'sound':'d'}, {self.y.name:True}),
        ({'name':'save_test6', 'sound':'c'}, {self.x.name:False, self.y.name:False}),
    ]))

    an = Animal.objects.create(name='save_test7',
        sound=JeevesLib.mkSensitive(self.x, 'b', 'c'))
    an.sound = JeevesLib.mkSensitive(self.y, 'd', 'e')
    with JeevesLib.PositiveVariable(self.x):
      with JeevesLib.PositiveVariable(self.y):
        an.save()
    a = list(Animal._objects_ordinary.filter(name='save_test7').all())
    self.assertTrue(areRowsEqual(a, [
        ({'name':'save_test7', 'sound':'d'}, {self.x.name:True, self.y.name:True}),
        ({'name':'save_test7', 'sound':'b'}, {self.x.name:True, self.y.name:False}),
        ({'name':'save_test7', 'sound':'c'}, {self.x.name:False}),
    ]))

  def testGet1():
    an = Animal.objects.create(name='get_test1', sound='b')

    bn = Animal.objects.get(name='get_test1')
    self.assertEqual(an.name, 'get_test1')
    self.assertEqual(an.sound, 'b')

    cn = Animal.objects.get(sound='b')
    self.assertEqual(cn.name, 'get_test1')
    self.assertEqual(cn.sound, 'b')

    self.assertEqual(an, bn)
    self.assertEqual(an, cn)
    self.assertEqual(bn, cn)

  def testGet2():
    an = Animal.objects.create(name='get_test2', sound=JeevesLib.mkSensitive(self.x, 'b', 'c'))

    bn = Animal.objects.get(name='get_test2')

    self.assertEqual(an == bn)
    self.assertEqual(an.name, 'get_test2')
    self.assertEqual(an.sound.cond.name, self.x.name)
    self.assertEqual(an.sound.thn.v, 'b')
    self.assertEqual(an.sound.thn.v, 'c')

  def testGet3():
    an = Animal.objects.create(name='get_test3', sound=JeevesLib.mkSensitive(self.x, JeevesLib.mkSensitive(self.y, 'b', 'c'), JeevesLib.mkSensitive(self.y, 'd', 'e')))

    bn = Animal.objects.get(name='get_test3')

    self.assertEqual(an == bn)
    self.assertEqual(JeevesLib.concretize((True,True), bn.sound), 'b')
    self.assertEqual(JeevesLib.concretize((True,False), bn.sound), 'c')
    self.assertEqual(JeevesLib.concretize((False,True), bn.sound), 'd')
    self.assertEqual(JeevesLib.concretize((False,False), bn.sound), 'e')

  def testGet4():
    with JeevesLib.PositiveVariable(self.x):
      an = Animal.objects.create(name='get_test4', sound='a')
    with JeevesLib.NegativeVariable(self.y):
      bn = Animal.objects.create(name='get_test4', sound='b')
    
    cn = Animal.objects.get(name='get_test4')
    self.assertEqual(cn.cond.name, self.x.name)
    self.assertEqual(cn.thn.v.name, 'get_test4')
    self.assertEqual(cn.thn.v.sound, 'a')
    self.assertEqual(cn.els.v.name, 'get_test4')
    self.assertEqual(cn.els.v.sound, 'b')

    an1 = cn.thn
    bn1 = cn.els
    self.assertTrue(an == an1)
    self.assertTrue(bn == bn1)
    self.assertTrue(an != bn)
    self.assertTrue(an != bn1)
    self.assertTrue(bn != an)
    self.assertTrue(bn != an1)

  def testFilter1():
    an = Animal.objects.create(name='filter_test1', sound='a')

    bl = Animal.objects.filter(name='filter_test1').get_jiter()
    self.assertEquals(bl, [(an, {})])

  def testFilter2():
    with JeevesLib.PositiveVariable(self.x):
      an = Animal.objects.create(name='filter_test2', sound='a')

    bl = Animal.objects.filter(name='filter_test2').get_jiter()
    self.assertEquals(bl, [(an, {self.x.name:True})])

  def testFilter3():
    with JeevesLib.PositiveVariable(self.x):
      an = Animal.objects.create(name='filter_test3', sound='a')
    with JeevesLib.NegativeVariable(self.y):
      bn = Animal.objects.create(name='filter_test3', sound='b')

    bl = Animal.objects.filter(name='filter_test2').order_by('sound').get_jiter()
    self.assertEquals(bl, [(an, {self.x.name:True}), (bn, {self.y.name:False})])

  def testFilter4():
    an = Animal.objects.create(name='filter_test3', sound='b')
    bn = Animal.objects.create(name='filter_test3', sound=JeevesLib.mkSensitive(self.x, 'a', 'c'))

    bl = Animal.objects.filter(name='filter_test2').order_by('sound').get_jiter()
    self.assertEquals(bl, [(an, {self.x.name:True}), (bn, {}), (an, {self.x.name:False})])


