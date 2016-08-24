from . import db
from flask.ext.login import UserMixin
from . import login_manager
from datetime import datetime

# 装饰器not_student_login 所需要的模块
from functools import wraps
from flask import _request_ctx_stack, abort, current_app, flash, redirect, request, session, url_for, \
    has_request_context
from flask.ext.login import current_user


# 此装饰器用于学生没有权限访问的页面
def not_student_login(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        elif current_user.roleId == 0:
            return redirect('/')
        return func(*args, **kwargs)

    return decorated_view


# 装饰器: 更新 InternshipInfor 实习状态
def update_intern_internStatus(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        now = datetime.now().date()
        db.session.execute('update InternshipInfor set internStatus=0 where start > "%s"' % now)
        db.session.execute('update InternshipInfor set internStatus=1 where start < "%s" and end > "%s"' % (now, now))
        db.session.execute('update InternshipInfor set internStatus=2 where end < "%s"' % now)
        return func(*args, **kwargs)

    return decorated_view


# 装饰器: 更新 InternshipInfor 日志审核状态
def update_intern_jourCheck(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        now = datetime.now().date()
        is_not_checked = db.session.execute(
            'select distinct internId from Journal where jourCheck=0 and workEnd < "%s"' % now)
        if is_not_checked:
            for x in is_not_checked:
                db.session.execute('update InternshipInfor set jourCheck=0 where Id=%s' % x.internId)
        return func(*args, **kwargs)

    return decorated_view


@login_manager.user_loader
def load_user(Id):
    return Teacher.query.get(Id) or Student.query.get(Id)


class Role(db.Model):
    __tablename__ = 'Role'
    roleId = db.Column(db.Integer, primary_key=True)
    roleName = db.Column(db.String(5), unique=True)
    permission = db.Column(db.String(8), unique=True)
    # backref='role'可代替Teacher的roleId
    roleDescribe = db.Column(db.String(200))
    teacher = db.relationship('Teacher', backref='role', lazy='dynamic')
    student = db.relationship('Student', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    # 对角色进行权限判断
    @staticmethod
    def can(role, permissions):
        if role.permission is not None:
            p = eval(role.permission)
        return (p & permissions) == permissions


class Teacher(db.Model, UserMixin):
    __tablename__ = 'Teacher'
    teaId = db.Column(db.String(10), primary_key=True)
    teaName = db.Column(db.String(4), index=True)
    teaSex = db.Column(db.String(2))
    roleId = db.Column(db.Integer, db.ForeignKey('Role.roleId'), default=1)
    password = db.Column(db.String(10))

    def get_id(self):
        return self.teaId

    # 对教师用户进行权限判断
    def can(self, permissions):
        if self.role.permission is not None:
            p = eval(self.role.permission)
        return (p & permissions) == permissions

    def __repr__(self):
        return '<Teacher %r>' % self.teaName

    # 创建大量虚拟信息
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint, choice
        import forgery_py

        seed()
        for i in range(count):
            teacher = Teacher(
                teaId=randint(20000000, 20160000),
                teaName=forgery_py.internet.user_name(True),
                teaSex=choice(['男', '女']),
                password='123')
            db.session.add(teacher)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class Student(db.Model, UserMixin):
    __tablename__ = 'Student'
    stuId = db.Column(db.String(20), primary_key=True)
    stuName = db.Column(db.String(10), index=True)
    institutes = db.Column(db.String(10))
    major = db.Column(db.String(10))
    grade = db.Column(db.String(10))
    sex = db.Column(db.String(2))
    classes = db.Column(db.String(10))
    internCheck = db.Column(db.Integer, default=0)
    jourCheck = db.Column(db.Integer, default=0)
    sumCheck = db.Column(db.Integer, default=0)
    roleId = db.Column(db.Integer, db.ForeignKey('Role.roleId'), default=0)
    password = db.Column(db.String(10))

    def get_id(self):
        return self.stuId

    # 对学生用户进行权限判断
    def can(self, permissions):
        if self.role.permission is not None:
            p = eval(self.role.permission)
        return (p & permissions) == permissions

    def __repr__(self):
        return '<Student %r>' % self.stuName

    # 创建大量虚拟信息
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint, choice
        import forgery_py

        seed()
        for i in range(count):
            student = Student(
                stuId=randint(201300000000, 201600000000),
                stuName=forgery_py.internet.user_name(True),
                institutes='计算机学院',
                major=choice(['计算机科学与技术', '网络工程', '软件工程', '信息科学与技术']),
                grade=choice([2013, 2014, 2015, 2016]),
                classes=randint(1, 10),
                sex=choice(['男', '女']),
                password='123'
            )
            db.session.add(student)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class ComInfor(db.Model):
    __tablename__ = 'ComInfor'
    comId = db.Column(db.Integer, primary_key=True)
    comName = db.Column(db.String(20))
    comBrief = db.Column(db.String(200))
    comAddress = db.Column(db.String(100))
    comUrl = db.Column(db.String(50))
    comMon = db.Column(db.String(10))
    comProject = db.Column(db.String(100))
    comStaff = db.Column(db.Integer)
    comContact = db.Column(db.String(10))
    comPhone = db.Column(db.String(20))
    comEmail = db.Column(db.String(20))
    comFax = db.Column(db.String(20))
    comDate = db.Column(db.DATETIME, default=datetime.now)
    students = db.Column(db.Integer, default=0)
    comCheck = db.Column(db.Integer, default=0)
    internshipinfor = db.relationship('InternshipInfor', backref='cominfor', lazy='dynamic')

    # 创建大量虚拟信息
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint, choice
        import forgery_py

        seed()
        for i in range(count):
            comInfor = ComInfor(comName=forgery_py.internet.user_name(True),
                                comBrief=forgery_py.lorem_ipsum.sentences(),
                                comAddress=forgery_py.address.city(), comUrl=forgery_py.internet.domain_name(),
                                comMon=randint(100, 10000), comProject=forgery_py.lorem_ipsum.word(),
                                comStaff=randint(100, 10000),
                                comContact=forgery_py.name.full_name(), comPhone=forgery_py.address.phone(),
                                comEmail=forgery_py.internet.email_address(user=None),
                                comFax=forgery_py.address.phone())
            db.session.add(comInfor)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class InternshipInfor(db.Model):
    __tablename__ = 'InternshipInfor'
    Id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200))
    address = db.Column(db.String(200))
    opinion = db.Column(db.String(250))
    start = db.Column(db.Date)
    end = db.Column(db.Date)
    internStatus = db.Column(db.Integer, index=True)
    time = db.Column(db.DATETIME, default=datetime.now())
    icheckTeaId = db.Column(db.String(8))
    internCheck = db.Column(db.Integer, default=0)
    internStatus = db.Column(db.Integer, default=0)
    icheckTime = db.Column(db.DATETIME)
    comId = db.Column(db.Integer, db.ForeignKey('ComInfor.comId'))
    stuId = db.Column(db.String(20), db.ForeignKey('Student.stuId'))
    jourCheck = db.Column(db.Integer, default=0)


# can be delete
class DirctTea(db.Model):
    __tablename__ = 'DirctTea'
    Id = db.Column(db.Integer, primary_key=True)
    teaId = db.Column(db.String(10))
    teaName = db.Column(db.String(10))
    teaDuty = db.Column(db.String(20))
    teaPhone = db.Column(db.String(15))
    teaEmail = db.Column(db.String(20))
    cteaName = db.Column(db.String(10))
    cteaDuty = db.Column(db.String(20))
    cteaPhone = db.Column(db.String(15))
    cteaEmail = db.Column(db.String(20))
    comId = db.Column(db.Integer, db.ForeignKey('ComInfor.comId'))
    stuId = db.Column(db.String(20), db.ForeignKey('Student.stuId'))


class SchDirTea(db.Model):
    __tablename__ = 'SchDirTea'
    Id = db.Column(db.Integer, primary_key=True)
    teaId = db.Column(db.String(10))
    steaName = db.Column(db.String(10))
    steaDuty = db.Column(db.String(20))
    steaPhone = db.Column(db.String(15))
    steaEmail = db.Column(db.String(20))
    stuId = db.Column(db.String(20), db.ForeignKey('Student.stuId'))


class ComDirTea(db.Model):
    __tablename__ = 'ComDirTea'
    Id = db.Column(db.Integer, primary_key=True)
    cteaName = db.Column(db.String(10))
    cteaDuty = db.Column(db.String(20))
    cteaPhone = db.Column(db.String(15))
    cteaEmail = db.Column(db.String(20))
    comId = db.Column(db.Integer, db.ForeignKey('ComInfor.comId'))
    stuId = db.Column(db.String(20), db.ForeignKey('Student.stuId'))


class Summary(db.Model):
    __tablename__ = 'Summary'
    internId = db.Column(db.Integer, primary_key=True)
    sumCheck = db.Column(db.Integer)
    sumCheckTeaId = db.Column(db.String(10))
    sumCheckTime = db.Column(db.DATETIME)
    sumCheckOpinion = db.Column(db.String(250))
    comScore = db.Column(db.Integer)
    schScore = db.Column(db.Integer)
    sumScore = db.Column(db.Integer)


class Journal(db.Model):
    __tablename__ = 'Journal'
    Id = db.Column(db.Integer, primary_key=True)
    stuId = db.Column(db.String(20), db.ForeignKey('Student.stuId'))
    comId = db.Column(db.Integer, db.ForeignKey('ComInfor.comId'))
    weekNo = db.Column(db.Integer, default=1)
    workStart = db.Column(db.DATE)
    workEnd = db.Column(db.DATE)
    mon = db.Column(db.String(500), default=' ')
    tue = db.Column(db.String(500), default=' ')
    wed = db.Column(db.String(500), default=' ')
    thu = db.Column(db.String(500), default=' ')
    fri = db.Column(db.String(500), default=' ')
    sat = db.Column(db.String(500), default=' ')
    sun = db.Column(db.String(500), default=' ')
    jcheckTeaId = db.Column(db.String(8))
    jourCheck = db.Column(db.Integer, default=0)
    jcheckTime = db.Column(db.DATETIME)
    internId = db.Column(db.Integer, db.ForeignKey('InternshipInfor.Id'))
    opinion = db.Column(db.String(500), default='')
    isoweek = db.Column(db.Integer)
    isoyear = db.Column(db.Integer)


class Permission:
    # 企业信息查询
    COM_INFOR_SEARCH = 0X0000001
    # 企业信息编辑
    COM_INFOR_EDIT = 0X0000002
    # 企业信息审核
    COM_INFOR_CHECK = 0X0000004

    # 实习企业信息列表
    INTERNSHIP_LIST = 0X0000008
    # 学生实习信息列表
    STU_INTERN_LIST = 0X0000010

    # 学生实习信息查看
    STU_INTERN_SEARCH = 0X0000020
    # 学生实习信息编辑
    STU_INTERN_EDIT = 0X0000040
    # 学生实习信息审核
    STU_INTERN_CHECK = 0X0000080
    # 学生实习信息导出
    STU_INTERN_EXPORT = 0X0000100

    # 学生实习日志查询
    STU_JOUR_SEARCH = 0X0000200
    # 学生实习日志编辑
    STU_JOUR_EDIT = 0X0000400
    # 学生实习日志审核
    STU_JOUR_CHECK = 0X0000800
    # 学生实习日志导出
    STU_JOUR_EXPORT = 0X0001000

    # 学生实习总结查看
    STU_SUM_SEARCH = 0X0002000
    # 学生实习总结编辑
    STU_SUM_EDIT = 0X0004000
    # 学生实习总结导出
    STU_SUM_EXPORT = 0X0008000
    # 学生实习总结和成果审核
    STU_SUM_SCO_CHECK = 0X0010000

    # 学生实习成果查看
    STU_SCO_SEARCH = 0X0020000
    # 学生实习成果编辑
    STU_SCO_EDIT = 0X0040000
    # 学生实习成果导出
    STU_SCO_EXPORT = 0X0080000

    # 管理
    ADMIN = 0X0100000
    # 学生信息导入
    STU_INTERN_IMPORT = 0X0200000
    # 老师信息导入
    TEA_INFOR_IMPORT = 0X0400000
    # 权限管理
    PERMIS_MANAGE = 0X0800000


