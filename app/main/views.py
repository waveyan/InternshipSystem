from flask import render_template, url_for, flash, redirect, request, session
from .form import searchForm, comForm, internshipForm, journalForm, stuForm, teaForm, permissionForm, schdirteaForm, \
    comdirteaForm
from . import main
from ..models import Permission, InternshipInfor, ComInfor, SchDirTea, ComDirTea, Student, Journal, Role, Teacher, not_student_login, update_intern_internStatus, update_intern_jourCheck
from flask.ext.login import current_user, login_required
from .. import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta, date

# datepicker failed
'''
from flask_wtf import Form

@main.route('/test', methods=['GET','POST'])
def hello_world():
    form = ExampleForm()
    if form.validate_on_submit():
        return form.dt.data.strftime('%Y-%m-%d')
    return render_template('example.html')
'''

# @main.route('/search', methods=['GET', 'POST'])
# def search():
#     form = searchForm()
#     if form.validate_on_submit():
#         print('assa')
#     print(form.key.data)
#     return render_template('index.html', form=form, Permission=Permission)


@main.route('/students', methods=['GET', 'POST'])
def students():
    form = searchForm()
    return render_template('students.html', form=form, Permission=Permission)


# 实习提交表
@main.route('/stuinfor', methods=['GET', 'POST'])
def stuinfor():
    return render_template('stuinfor.html', Permission=Permission)


@main.route('/journal', methods=['GET', 'POST'])
def journal():
    return render_template('journal.html', Permission=Permission)


@main.route('/summary', methods=['GET', 'POST'])
def summary():
    return render_template('summary.html', Permission=Permission)


# 评分表
@main.route('/score', methods=['GET', 'POST'])
def score():
    return render_template('score.html', Permission=Permission)


@main.route('/statistics', methods=['GET', 'POST'])
def statistics():
    return render_template('statistics.html', Permission=Permission)


# --------------------------------------------------------------------


# 首页
@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', Permission=Permission)



# 个人实习企业列表
@main.route('/stuInternList', methods=['GET', 'POST'])
@login_required
@update_intern_jourCheck
@update_intern_internStatus
def stuInternList():
    page = request.args.get('page', 1, type=int)
    if current_user.roleId == 0:
        stuId = current_user.stuId
        student = Student.query.filter_by(stuId=stuId).first()
        internship = InternshipInfor.query.filter_by(stuId=stuId).all()
        if internship is None:
            flash('您还没完成实习信息的填写，请完善相关实习信息！')
            return redirect(url_for('.addcominfor'))
        else:
            pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId==ComInfor.comId) \
                .add_columns(ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck) \
                .filter(InternshipInfor.stuId==stuId).order_by(func.field(InternshipInfor.internStatus,1,0,2)).paginate(page, per_page=8, error_out=False)
            internlist = pagination.items
            return render_template('stuInternList.html', internlist=internlist, Permission=Permission, internship=internship, student=student, pagination=pagination)
    elif current_user.can(Permission.STU_INTERN_SEARCH):
        pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId==ComInfor.comId).join(Student, Student.stuId==InternshipInfor.stuId) \
            .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck) \
            .order_by(func.field(InternshipInfor.internStatus,1,0,2)).paginate(page, per_page=8, error_out=False)
        internlist = pagination.items
        return render_template('stuInternList.html', internlist=internlist, Permission=Permission, pagination=pagination)
    else:
        flash('非法操作')
        return redirect('/')


# 选择实习企业
@main.route('/selectCom', methods=['GET', 'POST'])
@login_required
def selectCom():
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    pagination = ComInfor.query.filter_by(comCheck=2).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    return render_template('selectCom.html', form=form, Permission=Permission, comInfor=comInfor, pagination=pagination)


# 添加企业信息
@main.route('/addcominfor', methods=['GET', 'POST'])
@login_required
def addcominfor():
    form = comForm()
    if form.validate_on_submit():
        max_comId = getMaxComId()
        if max_comId is None:
            max_comId = 1
        else:
            max_comId = max_comId + 1
        try:
            # 如果有企业信息审核权限的用户添加企业信息自动通过审核
            if current_user.can(Permission.COM_INFOR_CHECK):
                comInfor = ComInfor(comName=form.comName.data, comBrief=form.comBrief.data,
                                    comAddress=form.comAddress.data,
                                    comUrl=form.comUrl.data, comMon=form.comMon.data, comContact=form.comContact.data,
                                    comProject=form.comProject.data, comStaff=form.comStaff.data,
                                    comPhone=form.comPhone.data,
                                    comEmail=form.comEmail.data, comFax=form.comFax.data, comCheck=2)
            else:
                comInfor = ComInfor(comName=form.comName.data, comBrief=form.comBrief.data,
                                    comAddress=form.comAddress.data,
                                    comUrl=form.comUrl.data, comMon=form.comMon.data, comContact=form.comContact.data,
                                    comProject=form.comProject.data, comStaff=form.comStaff.data,
                                    comPhone=form.comPhone.data,
                                    comEmail=form.comEmail.data, comFax=form.comFax.data)
            print('true')
            db.session.add(comInfor)
            db.session.commit()
            flash('实习企业信息添加成功！')
            if current_user.roleId == 0:
                return redirect(url_for('.addInternship', comId=max_comId))
            else:
                return redirect(url_for('.interncompany'))
        except Exception as e:
            db.session.rollback()
            print('实习企业信息：', e)
            flash('实习企业信息提交失败，请重试！')
            return redirect(url_for('.addcominfor'))
    return render_template('addcominfor.html', form=form, Permission=Permission)


# 添加实习信息
# 只能学生本人添加
@main.route('/addInternship', methods=['GET', 'POST'])
@login_required
def addInternship():
    comId = request.args.get('comId')
    iform = internshipForm()
    schdirteaform = schdirteaForm()
    comdirteaform = comdirteaForm()
    i = 0
    j = 0
    try:
        if request.method == 'POST':
            start = datetime.strptime(request.form.get('start'), '%Y-%m-%d').date()
            end = datetime.strptime(request.form.get('end'), '%Y-%m-%d').date()
            now = datetime.now().date()
            if start < now :
                if end <= now :
                    internStatus = 2 # 实习结束
                    print ('this is 1')
                if end > now :
                    internStatus = 1 #实习中
                    print ('this is 2')
            elif start > now :
                internStatus = 0 #待实习
                print ('this is 3')
            else:
                internStatus = 1  # start=now, 实习中
                print('this is 4')
            internship = InternshipInfor(
                task=request.form.get('task'),
                start=start,
                end=end,
                time=datetime.now().date(),
                address=request.form.get('address'),
                comId=comId,
                stuId=current_user.stuId,
                internStatus=internStatus
            )
            db.session.add(internship)
            try:
                db.session.commit()
            except Exception as e:
                print('添加实习信息：', e)
                db.session.rollback()
                flash('添加实习信息失败，请重试！')
            while True:
                i = i + 1
                j = j + 1
                teaValue = request.form.get('teaId%s' % i)
                print(teaValue)
                cteaValue = request.form.get('cteaName%s' % j)
                print(cteaValue)
                if teaValue:
                    print(teaValue)
                    schdirtea = SchDirTea(
                        teaId=teaValue,
                        stuId=current_user.stuId,
                        teaName=request.form.get('teaName%s' % i),
                        teaDuty=request.form.get('teaDuty%s' % i),
                        teaPhone=request.form.get('teaPhone%s' % i),
                        teaEmail=request.form.get('teaEmail%s' % i)
                    )
                    db.session.add(schdirtea)
                    if cteaValue:
                        print(cteaValue)
                        comdirtea = ComDirTea(
                            stuId=current_user.stuId,
                            teaName=cteaValue,
                            comId=comId,
                            teaDuty=request.form.get('cteaDuty%s' % j),
                            teaEmail=request.form.get('cteaEmail%s' % j),
                            teaPhone=request.form.get('cteaPhone%s' % j)
                        )
                        db.session.add(comdirtea)
                elif cteaValue:
                    print(cteaValue)
                    comdirtea = ComDirTea(
                        stuId=current_user.stuId,
                        teaName=cteaValue,
                        comId=comId,
                        teaDuty=request.form.get('cteaDuty%s' % j),
                        teaEmail=request.form.get('cteaEmail%s' % j),
                        teaPhone=request.form.get('cteaPhone%s' % j)
                    )
                    db.session.add(comdirtea)
                    if teaValue:
                        print(teaValue)
                        schdirtea = SchDirTea(
                            teaId=teaValue,
                            stuId=current_user.stuId,
                            teaName=request.form.get('teaName%s' % i),
                            teaDuty=request.form.get('teaDuty%s' % i),
                            teaPhone=request.form.get('teaPhone%s' % i),
                            teaEmail=request.form.get('teaEmail%s' % i)
                        )
                        db.session.add(schdirtea)


            # commit internship之后,internId才会更新
            try:
                db.session.add(internship)
                db.session.commit()
            except Exception as e:
                print('添加指导老师：', e)
                db.session.rollback()
                flash('添加实习信息失败，请重试！')

            # 初始化实习日志
            internId = int(InternshipInfor.query.order_by(desc(InternshipInfor.Id)).first().Id)
            weeks = end.isocalendar()[1] - start.isocalendar()[1] + 1
            if weeks > 1:
                # 第一周. 因第一天未必是周一,所以需特别处理
                journal = Journal(
                    stuId=current_user.stuId,
                    comId=comId,
                    weekNo=1,
                    workStart=start,
                    workEnd=start + timedelta(days=(7 - start.isoweekday())),
                    internId=internId
                )
                db.session.add(journal)
                start = start + timedelta(days=(7 - start.isoweekday() + 1))
                # 第二周至第 n|(n-1) 周
                for weekNo in range(weeks - 2):
                    journal = Journal(
                        stuId=current_user.stuId,
                        comId=comId,
                        weekNo=weekNo + 2,
                        workStart=start,
                        workEnd=start + timedelta(days=6),
                        internId=internId
                    )
                    db.session.add(journal)
                    start = start + timedelta(days=7)
                # 如果还有几天凑不成一周
                if end >= start:
                    journal = Journal(
                        stuId=current_user.stuId,
                        comId=comId,
                        weekNo=weeks,
                        workStart=start,
                        workEnd=end,
                        internId=internId
                    )
                    db.session.add(journal)
            else:
                # 如果实习时间不满一周
                journal = Journal(
                    stuId=current_user.stuId,
                    comId=comId,
                    weekNo=1,
                    workStart=start,
                    workEnd=end,
                    internId=internId
                )
                db.session.add(journal)

            # 更新累计实习人数
            cominfor = ComInfor.query.filter_by(comId=comId).first()
            if cominfor.students:
                cominfor.students = int(cominfor.students) + 1
            else:
                cominfor.students = 1
            db.session.add(cominfor)
            db.session.commit()
            flash('提交实习信息成功！')
            return redirect(url_for('.stuInternList'))
    except Exception as e:
        print("实习信息：", e)
        db.session.rollback
        flash('提交实习信息失败，请重试！')
        return redirect(url_for('.addcominfor'))
    return render_template('addinternship.html', iform=iform, schdirteaform=schdirteaform, comdirteaform=comdirteaform,
                           Permission=Permission)


# 学生个人实习信息
@main.route('/xIntern', methods=['GET','POST'])
@login_required
def xIntern():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.args.get('stuId')
    comId = request.args.get('comId')
    internId = request.args.get('internId')
    student = Student.query.filter_by(stuId=stuId).first()
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    comInfor = ComInfor.query.filter_by(comId=comId).first()
    schdirtea = SchDirTea.query.filter_by(stuId=stuId).all()
    comdirtea = ComDirTea.query.filter_by(stuId=stuId, comId=comId).all()
    return render_template('xIntern.html', Permission=Permission, comInfor=comInfor,
                           schdirtea=schdirtea, comdirtea=comdirtea, internship=internship, student=student)


# 审核通过实习信息
@main.route('/xIntern_comfirm', methods=["POST","GET"])
@not_student_login
def xIntern_comfirm():
    if current_user.can(Permission.STU_INTERN_CHECK):
        internId = request.form.get('internId')
        internCheck = request.form.get('internCheck')
        stuId = request.form.get('stuId')
        opinion = request.form.get('opinion')
        try:
            if opinion:
                db.session.execute('update InternshipInfor set internCheck=%s, opinion="%s" where Id=%s' % (internCheck, opinion, internId))
            else:
                db.session.execute('update InternshipInfor set internCheck=%s where Id=%s' % (internCheck, internId))
        except Exception as e:
            db.session.rollback()
            print(datetime.now(),":", current_user.get_id(), "审核日志失败", e)
            flash("实习申请审核失败")
            return redirect("/")
        flash("实习申请审核成功")
    return redirect(url_for('.stuInternList', stuId=stuId))


# 修改实习信息
@main.route('/xInternEdit', methods=['GET','POST'])
@login_required
def xInternEdit():
    if current_user.roleId==0:
        stuId = current_user.stuId
    elif not current_user.can(Permission.STU_INTERN_EDIT):
        flash('非法操作')
        return redirect('/')
    if request.form.get('stuId'):
        stuId = request.form.get('stuId')
        comId = request.form.get('comId')
        internId = request.form.get('internId')
    else:
        stuId = request.args.get('stuId')
        comId = request.args.get('comId')
        internId = request.args.get('internId')
    student = Student.query.filter_by(stuId=stuId).first()
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    comInfor = ComInfor.query.filter_by(comId=comId).first()
    schdirtea = SchDirTea.query.filter_by(stuId=stuId).all()
    comdirtea = ComDirTea.query.filter_by(stuId=stuId, comId=comId).all()
    # 各种Form
    stuform = stuForm()
    comform = comForm()
    internform = internshipForm()
    schdirteaform = schdirteaForm()
    comdirteaform = comdirteaForm()
    return render_template('xInternEdit.html', Permission=Permission, comInfor=comInfor, schdirtea=schdirtea, \
        comdirtea=comdirtea, internship=internship, student=student, stuform=stuform, comform=comform, \
        internform=internform, schdirteaform=schdirteaform, comdirteaform=comdirteaform)



# 修改实习信息 个人实习信息--实习岗位信息
@main.route('/xInternEdit_intern', methods=["POST","GET"])
@login_required
def xInternEdit_intern():
    if current_user.roleId == 0:
        stuId = current_user.stuId
        internCheck = 0
    elif current_user.can(Permission.STU_INTERN_CHECK):
        stuId = request.form.get('stuId')
        internCheck = 1
    task = request.form.get('task')
    address = request.form.get('address')
    start = request.form.get('start')
    end = request.form.get('end')
    time = datetime.now().date()
    comId = request.form.get("comId")
    internId = request.form.get("internId")
    if task is None or address is None or start is None or end is None or time is None or comId is None or stuId is None or internId is None:
        flash("修改实习信息失败,请重试")
        return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))
    db.session.execute(' \
        update InternshipInfor set \
        task = "%s", \
        address = "%s", \
        start = "%s", \
        end = "%s", \
        time = "%s", \
        internCheck = %s \
        where Id=%s'
                       % (task, address, start, end, time, internCheck, internId)
                       )

    # 实习信息修改,日志跟随变动
    # 先删除原来的日志
    db.session.execute("delete from Journal where internId=%s" % internId)
    # 初始化实习日志
    start = datetime.strptime(start, '%Y-%m-%d').date()
    end = datetime.strptime(end, '%Y-%m-%d').date()
    weeks = end.isocalendar()[1] - start.isocalendar()[1] + 1
    if weeks > 1:
        # 第一周. 因第一天未必是周一,所以需特别处理
        journal = Journal(
            stuId = stuId,
            comId = comId,
            weekNo = 1,
            workStart = start,
            workEnd = start + timedelta(days=(7 - start.isoweekday())),
            internId = internId
            )

        db.session.add(journal)
        start = start + timedelta(days=(7 - start.isoweekday() + 1))
        # 第二周至第 n|(n-1) 周
        for weekNo in range(weeks - 2):
            journal = Journal(
                stuId = stuId,
                comId = comId,
                weekNo = weekNo+2,
                workStart = start,
                workEnd = start + timedelta(days=6),
                internId = internId
                )
            db.session.add(journal)
            start = start + timedelta(days=7)
        # 如果还有几天凑不成一周
        if end >= start:
            journal = Journal(
                stuId = stuId,
                comId = comId,
                weekNo = weeks,
                workStart = start,
                workEnd = end,
                internId = internId
                )
            db.session.add(journal)
    else:
        # 如果实习时间不满一周
        journal = Journal(
            stuId = stuId,
            comId = comId,
            weekNo = 1,
            workStart = start,
            workEnd = end,
            internId = internId
            )
        db.session.add(journal)

    flash("实习信息修改成功")
    return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))


# 修改实习信息 个人实习信息--企业指导老师
@main.route('/xInternEdit_comdirtea', methods=["POST"])
@login_required
def xInternEdit_comdirtea():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.form.get('stuId')
    Id = request.form.get("Id")
    comId = request.form.get('comId')
    start = request.form.get('start')
    teaName = request.form.get('cteaName')
    teaDuty = request.form.get('cteaDuty')
    teaPhone = request.form.get('cteaPhone')
    teaEmail = request.form.get('cteaEmail')
    internId = request.form.get("internId")
    print(internId)
    print(stuId)
    if teaName is None or comId is None or internId is None or stuId is None:
        flash("修改实习信息失败,请重试")
        return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))
    db.session.execute(' \
        update ComDirTea set \
        teaName = "%s", \
        teaDuty = "%s", \
        teaPhone ="%s", \
        teaEmail = "%s" \
        where Id=%s'
                       % (teaName, teaDuty, teaPhone, teaEmail, Id)
                       )
    flash("实习信息修改成功")
    return redirect(url_for('.xIntern', comId=comId, internId=internId, stuId=stuId))


# 修改实习信息 删除整个实习页面
@main.route('/comfirmDeleteJournal_Intern', methods=['POST'])
@login_required
def comfirmDeletreJournal_Intern():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.form.get('stuId')
    internId = request.form.get('internId')
    from_url = request.form.get('from_url')
    try:
        # 企业指导老师,日志,实习一同删除
        comId = InternshipInfor.query.filter_by(Id=internId).first().comId
        db.session.execute('delete from ComDirTea where stuId="%s" and comId=%s'% (stuId, comId))
        db.session.execute('delete from Journal where internId=%s and stuId=%s'% (internId, stuId))
        db.session.execute('delete from InternshipInfor where Id=%s and stuId=%s'% (internId, stuId))
        # 企业累计实习人数减一
        db.session.execute('update ComInfor set students = students -1 where comId=%s'% temp_comId)
        flash('删除日志和实习信息成功')
        if from_url == "/xIntern":
            return redirect(url_for('.stuInternList'))
        if from_url == "/xJournal":
            return redirect(url_for('.stuJournalList'))
    except Exception as e:
        print('删除日志和实习信息失败:', e)
        db.session.rollback
        flash('提交实习信息失败，请重试！')
        if from_url == "/xIntern":
            return redirect(url_for('.stuInternList'))
        elif from_url == "/xJournal":
            return redirect(url_for('.stuJournalList'))
    return redirect('/')


# 企业详细信息,方法POST不可删除，在修改返回时有用
@main.route('/cominfor', methods=['GET', 'POST'])
@login_required
def cominfor():
    id = request.args.get('id')
    com = ComInfor.query.filter_by(comId=id).first()
    return render_template('cominfor.html', Permission=Permission, com=com)



# 实习企业列表
@main.route('/interncompany', methods=['GET', 'POST'])
@login_required
def interncompany():
    form = searchForm()
    if request.method == 'POST':
        return redirect(url_for('.search', key=form.key.data, me='intern'))
    city = {}
    page = request.args.get('page', 1, type=int)
    com = create_com_filter(city)
    pagination = com.paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    return render_template('interncompany.html', form=form, Permission=Permission, pagination=pagination,
                           comInfor=comInfor, city=city)




# 企业信息用户操作筛选项,对所选筛选项进行删除
@main.route('/update_filter', methods=['GET', 'POST'])
@login_required
def update_filter():
    city = request.args.get('city')
    name = request.args.get('name')
    students = request.args.get('students')
    flag = request.args.get('flag')
    if city is not None:
        session['name'] = None
        session['students'] = None
        session['status'] = None
    elif name is not None:
        session['students'] = None
        session['status'] = None
    elif students is not None:
        session['status'] = None
    else:
        session['city'] = None
        session['name'] = None
        session['students'] = None
        session['status'] = None
    if flag == '1':
        return redirect(url_for('.allcomCheck'))
    elif flag == '0':
        return redirect(url_for('.allcomDelete'))
    else:
        return redirect(url_for('.interncompany'))



# 搜索,只对企业名称存在的关键字作搜索
@main.route('/search/<key>', methods=['GET', 'POST'])
@login_required
def search(key):
    form = searchForm()
    if current_user.can(Permission.COM_INFOR_CHECK):
        if request.args.get('me') == 'intern':
            cominfor = ComInfor.query.all()
            comInfor = []
            num = 0
            for c in cominfor:
                if c.comName.find(key) != -1:
                    comInfor.append(c)
                    num = num + 1
    elif request.args.get('me') == 'intern':
        cominfor = ComInfor.query.filter_by(comCheck=2).all()
        comInfor = []
        num = 0
        for c in cominfor:
            if c.comName.find(key) != -1:
                comInfor.append(c)
                num = num + 1
    return render_template('searchResult.html', num=num, form=form, Permission=Permission, comInfor=comInfor, key=key)


# 填写实习日志
@main.route('/addjournal/<int:comId>', methods=['GET', 'POST'])
@login_required
def addjournal(comId):
    form = journalForm()
    if form.validate_on_submit():
        # workend = datetime.strptime(form.workStart.data, '%Y-%m-%d').date()
        workend = form.workStart.data
        journal = Journal(
            stuId=current_user.stuId,
            workStart=form.workStart.data.strftime('%Y-%m-%d'),
            weekNo=form.weekNo.data,
            workEnd=workend,
            comId=comId,
            mon=form.mon.data,
            tue=form.tue.data,
            wed=form.wed.data,
            thu=form.thu.data,
            fri=form.fri.data,
            sat=form.sat.data,
            sun=form.sun.data)
        db.session.add(journal)
        try:
            db.session.commit()
            flash('提交成功！')
            return redirect(url_for('.myjournal', comId=comId))
        except Exception as e:
            db.session.rollback()
            print('日志提交失败：', e)
            flash('提交失败！')
    return render_template('addjournal.html', Permission=Permission, form=form)


# 管理员\普通教师\审核教师
# 特定企业的实习学生列表
@main.route('/comInternList/<int:comId>', methods=['GET', 'POST'])
@login_required
def studentList(comId):
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    comName = ComInfor.query.filter(ComInfor.comId == comId).with_entities(ComInfor.comName).first()[0]
    # filter过滤当前特定企业ID
    pagination = Student.query.join(InternshipInfor).filter(InternshipInfor.comId == comId).order_by(
        Student.grade).paginate(page, per_page=8, error_out=False)
    student = pagination.items
    for stu in student:
        internStatus = InternshipInfor.query.filter_by(comId=comId, stuId=stu.stuId, internStatus=0).count()
        session[stu.stuId] = internStatus
    return render_template('studentList.html', form=form, pagination=pagination, student=student, Permission=Permission, comId=comId, comName=comName)


# 单条审核企业信息
@main.route('/com_comfirm', methods=['GET', 'POST'])
@not_student_login
def com_comfirm():
    if not current_user.can(Permission.COM_INFOR_CHECK):
        return redirect(url_for('.interncompany'))
    else:
        comId = request.args.get('comId')
        check = request.args.get('check')
        print(check)
        com = ComInfor.query.filter_by(comId=comId).first()
        if check == 'pass':
            com.comCheck = 2
            str = '审核成功，一条信息审核通过。'
            print(str)
        else:
            com.comCheck = 1
            str = '审核成功，一条信息审核未通过。'
        try:
            db.session.add(com)
            db.session.commit()
            flash(str)
            return redirect(url_for(('.interncompany')))
        except Exception as e:
            print('企业信息单条审核：', e)
            db.session.rollback()
            flash('审核失败，请重试！')
            return redirect(url_for(('.interncompany')))


# 批量审核企业信息
@main.route('/allcomCheck', methods=['GET', 'POST'])
@not_student_login
def allcomCheck():
    if not current_user.can(Permission.COM_INFOR_CHECK):
        flash("非法操作")
        return redirect('.interncompany')
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    city = {}
    com = create_com_filter(city, flag=False)
    pagination = com.order_by(ComInfor.comDate).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    # 确定企业审核通过
    if request.method == "POST":
        comId = request.form.getlist('approve[]')
        for x in comId:
            db.session.execute("update ComInfor set comCheck=2 where comId = %s" % x)
        return redirect(url_for('.allcomCheck', page=pagination.page))
    return render_template('allcomCheck.html', form=form, Permission=Permission, comInfor=comInfor,
                           pagination=pagination, city=city)


# 单条删除企业信息
@main.route('/com_delete', methods=['GET', 'POST'])
@not_student_login
def com_delete():
    if not current_user.can(Permission.COM_INFOR_CHECK):
        return redirect(url_for('.interncompany'))
    else:
        if request.method == 'POST':
            comId = str(request.form.get('comId'))
            print(comId)
            com = ComInfor.query.filter_by(comId=comId).first()
            if com.students != 0:
                flash('此企业信息存在学生的实习信息，不能删除，如要删除请先删除相关学生实习信息！')
                return redirect(url_for('.interncompany'))
            else:
                try:
                    db.session.execute("delete from ComInfor WHERE comId=%s" % comId)
                    flash("删除成功！")
                    return redirect(url_for(('.interncompany')))
                except Exception as e:
                    print('企业信息单条删除：', e)
                    db.session.rollback()
                    flash('删除失败，请重试！')
                    return redirect(url_for(('.interncompany')))


# 批量删除企业信息
@main.route('/allcomDelete', methods=['GET', 'POST'])
@not_student_login
def allcomDelete():
    if not current_user.can(Permission.COM_INFOR_CHECK):
        return redirect('.interncompany')
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    # 只有无人实习的企业,或者实习信息被清空的企业,才能被删除
    city = {}
    com = create_com_filter(city)
    pagination = com.filter_by(students=0).order_by(ComInfor.comDate.desc()).paginate(page, per_page=8, error_out=False)
    comInfor = pagination.items
    # 确定企业删除
    if request.method == "POST":
        comId = request.form.getlist('approve[]')
        for x in comId:
            db.session.execute("delete from ComInfor where comId = %s" % x)
        return redirect(url_for('.allcomDelete', page=pagination.page))
    return render_template('allcomDelete.html', form=form, Permission=Permission, comInfor=comInfor,  pagination=pagination, city=city)


# 修改实习信息，没有考虑学生修改自己的企业信息
@main.route('/editcominfor', methods=['GET', 'POST'])
@not_student_login
def editcominfor():
    comform = comForm()
    id = request.args.get('comId')
    com = ComInfor.query.filter_by(comId=id).first()
    if request.method == 'POST':
        print(comform.comName.data)
        com.comName = comform.comName.data
        com.comAddress = comform.comAddress.data
        com.comUrl = comform.comUrl.data
        com.comBrief = request.form.get('text')
        com.comProject = comform.comProject.data
        com.comMon = comform.comMon.data
        com.comStaff = comform.comStaff.data
        com.comContact = comform.comContact.data
        com.comPhone = comform.comPhone.data
        com.comEmail = comform.comEmail.data
        com.comFax = comform.comFax.data
        try:
            db.session.add(com)
            db.session.commit()
            flash('修改成功！')
            return redirect(url_for('.cominfor', id=id))
        except Exception as e:
            db.session.rollback()
            flash('修改失败，请重试！')
            return redirect(url_for('.editcominfor', comId=id))
    return render_template('editComInfor.html', Permission=Permission, com=com, comform=comform)


# 批量审核实习信息
@main.route('/stuIntern_allCheck', methods=['GET', 'POST'])
@not_student_login
def stuIntern_allCheck():
    if not current_user.can(Permission.STU_INTERN_CHECK):
        flash("非法操作")
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId==ComInfor.comId).join(Student, Student.stuId==InternshipInfor.stuId) \
        .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck) \
        .filter(InternshipInfor.internCheck!=2).order_by(InternshipInfor.internStatus).paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    # 确定实习审核通过
    if request.method == "POST":
        internId = request.form.getlist('approve[]')
        for x in internId:
            db.session.execute('update InternshipInfor set internCheck=2 where Id = %s' % x)
        flash('实习信息审核成功')
        return redirect(url_for('.stuIntern_allCheck', page=pagination.page))
    return render_template('stuIntern_allCheck.html', Permission=Permission, internlist=internlist, pagination=pagination)


# 批量删除实习信息
@main.route('/stuIntern_allDelete', methods=['GET', 'POST'])
@not_student_login
def stuIntern_allDelete():
    if not current_user.can(Permission.STU_INTERN_CHECK):
        flash("非法操作")
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId==ComInfor.comId).join(Student, Student.stuId==InternshipInfor.stuId) \
        .add_columns(InternshipInfor.stuId, Student.stuName, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck) \
        .order_by(InternshipInfor.internCheck, InternshipInfor.internStatus).paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    # 确定删除实习
    if request.method == "POST":
        internId = request.form.getlist('approve[]')
        for x in internId:
            # 企业指导老师,日志,实习一同删除
            temp_intern = InternshipInfor.query.filter_by(Id=x).first()
            temp_comId = temp_intern.comId
            temp_stuId = temp_intern.stuId
            db.session.execute('delete from ComDirTea where stuId="%s" and comId=%s'% (temp_stuId, temp_comId))
            db.session.execute('delete from Journal where internId=%s'% x)
            db.session.execute('delete from InternshipInfor where Id=%s'% x)
            # 企业累计实习人数减一
            db.session.execute('update ComInfor set students = students -1 where comId=%s'% temp_comId)
        flash('实习信息删除成功')
        return redirect(url_for('.stuIntern_allDelete', page=pagination.page))
    return render_template('stuIntern_allDelete.html', Permission=Permission, internlist=internlist, pagination=pagination)


# 批量审核日志
@main.route('/stuJournal_allCheck', methods=['GET', 'POST'])
@not_student_login
def stuJournal_allCheck():
    if not current_user.can(Permission.STU_INTERN_CHECK):
        flash("非法操作")
        return redirect('/')
    now = datetime.now().date()
    page = request.args.get('page', 1, type=int)
    pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId==ComInfor.comId).join(Journal, InternshipInfor.Id==Journal.internId).join(Student, InternshipInfor.stuId==Student.stuId) \
        .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.jourCheck) \
        .filter(InternshipInfor.internCheck==2, InternshipInfor.internStatus !=0, InternshipInfor.jourCheck==0).group_by(InternshipInfor.Id).order_by(func.field(InternshipInfor.internStatus,1,0,2)).paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    # 确定日志审核通过
    if request.method == "POST":
        internId = request.form.getlist('approve[]')
        for x in internId:
            db.session.execute('update InternshipInfor set jourCheck=1 where Id=%s'% x)
            db.session.execute('update Journal set jourCheck=1 where internId=%s and workEnd<"%s"'% (x, now))
        flash('日志审核成功')
        return redirect(url_for('.stuJournal_allCheck', page=pagination.page))
    return render_template('stuJournal_allCheck.html', Permission=Permission, pagination=pagination, internlist=internlist)


# 批量删除日志
@main.route('/stuJournal_allDelete', methods=['GET', 'POST'])
@not_student_login
def stuJournal_allDelete():
    if not current_user.can(Permission.STU_INTERN_CHECK):
        flash("非法操作")
        return redirect('/')
    now = datetime.now().date()
    page = request.args.get('page', 1, type=int)
    pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId==ComInfor.comId).join(Journal, InternshipInfor.Id==Journal.internId).join(Student, InternshipInfor.stuId==Student.stuId) \
        .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.jourCheck) \
        .filter(InternshipInfor.internCheck==2).group_by(InternshipInfor.Id).order_by(func.field(InternshipInfor.internStatus,1,0,2)).paginate(page, per_page=8, error_out=False)
    # pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId==ComInfor.comId).join(Journal, InternshipInfor.Id==Journal.internId).join(Student, InternshipInfor.stuId==Student.stuId) \
        # .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.jourCheck) \
        # .filter(InternshipInfor.internCheck==2, InternshipInfor.internStatus !=0).group_by(InternshipInfor.Id).order_by(func.field(InternshipInfor.internStatus,1,0,2)).paginate(page, per_page=8, error_out=False)
    internlist = pagination.items
    # 确定删除日志
    if request.method == "POST":
        internId = request.form.getlist('approve[]')
        for x in internId:
            # 企业指导老师,日志,实习一同删除
            temp_intern = InternshipInfor.query.filter_by(Id=x).first()
            temp_comId = temp_intern.comId
            temp_stuId = temp_intern.stuId
            db.session.execute('delete from ComDirTea where stuId="%s" and comId=%s'% (temp_stuId, temp_comId))
            db.session.execute('delete from Journal where internId=%s'% x)
            db.session.execute('delete from InternshipInfor where Id=%s'% x)
            # 企业累计实习人数减一
            db.session.execute('update ComInfor set students = students -1 where comId=%s'% temp_comId)
        flash('日志删除成功')
        return redirect(url_for('.stuJournal_allDelete', page=pagination.page))
    return render_template('stuJournal_allDelete.html', Permission=Permission, pagination=pagination, internlist=internlist)
    


# 学生日志 -- 包含所有实习学生的列表
@main.route('/stuJournalList', methods=['GET', 'POST'])
@login_required
def stuJournalList():
    page = request.args.get('page', 1, type=int)
    if current_user.roleId == 0:
        stuId = current_user.stuId
        internship = InternshipInfor.query.filter_by(stuId=stuId).all()
        if internship is None:
            flash('目前还没有通过审核的实习信息,请完善相关实习信息,或耐心等待审核通过')
            return redirect(url_for('/'))
        else:
            pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId==ComInfor.comId).join(Journal, InternshipInfor.Id==Journal.internId).join(Student, InternshipInfor.stuId==Student.stuId) \
                .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.jourCheck) \
                .filter(InternshipInfor.stuId==stuId, InternshipInfor.internCheck==2).group_by(InternshipInfor.Id).order_by(func.field(InternshipInfor.internStatus,1,0,2)).paginate(page, per_page=8, error_out=False)            
            internlist = pagination.items
            return render_template('stuJournalList.html', internlist=internlist, Permission=Permission, pagination=pagination)
    elif current_user.can(Permission.STU_JOUR_SEARCH):
        pagination = InternshipInfor.query.join(ComInfor, InternshipInfor.comId==ComInfor.comId).join(Journal, InternshipInfor.Id==Journal.internId).join(Student, InternshipInfor.stuId==Student.stuId) \
            .add_columns(Student.stuName, Student.stuId, ComInfor.comName, InternshipInfor.comId, InternshipInfor.Id, InternshipInfor.start, InternshipInfor.end, InternshipInfor.internStatus, InternshipInfor.internCheck, InternshipInfor.jourCheck) \
            .filter(InternshipInfor.internCheck==2).group_by(InternshipInfor.Id).order_by(func.field(InternshipInfor.internStatus,1,0,2)).paginate(page, per_page=8, error_out=False)
        internlist = pagination.items
        return render_template('stuJournalList.html', internlist=internlist, Permission=Permission, pagination=pagination)


# 学生日志 -- 特定学生的日志详情
@main.route('/xJournal', methods=['GET', 'POST'])
@login_required
def xJournal():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    else:
        stuId = request.args.get('stuId')
    internId = request.args.get('internId')
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    student = Student.query.filter_by(stuId=stuId).first()
    # 获得当前时间对应的页码
    now = datetime.now().date()
    cur_page = Journal.query.filter(Journal.stuId==stuId, Journal.internId==internId, Journal.workStart<=now, Journal.workEnd>=now).first()
    if cur_page:
        page = request.args.get('page', cur_page.weekNo, type=int)
    else:
        page = request.args.get('page', 1 , type=int)

    pagination = Journal.query.filter_by(internId=internId).paginate(page, per_page=1, error_out=False)
    journal = pagination.items
    # journal = Journal.query.filter_by(stuId=stuId, internId=internId).all()
    comInfor = db.session.execute('select * from ComInfor where comId in( \
        select comId from InternshipInfor where Id=%s)'% internId).first()
    if internship.internCheck == 2:
        return render_template('xJournal.html', Permission=Permission, internship=internship, journal=journal, student=student, comInfor=comInfor, pagination=pagination, page=page, now=now)
    else:
        flash("实习申请需审核后,才能查看日志")
        return redirect(url_for('.xJournalList', stuId=stuId))


@main.route('/journal_comfirm', methods=['POST', 'GET'])
@not_student_login
def journal_comfirm():
    # 参数都是为了跳转 /xJournal 做准备
    stuId = request.args.get('stuId')
    jourId = request.args.get('jourId')
    internId = request.args.get('internId')    
    if current_user.can(Permission.STU_JOUR_CHECK):
        db.session.execute('update Journal set jourCheck=1 where Id=%s'% jourId)
        # 检查是否需要更新 InternshipInfor.jourCheck
        jourCheck = Journal.query.filter(Journal.internId==internId, Journal.jourCheck==0, Journal.workEnd < datetime.now().date()).count()
        if jourCheck == 0:
            db.session.execute('update InternshipInfor set jourCheck=1 where Id=%s'% internId)

        flash("日志审核通过")
        return redirect(url_for('.stuJournalList'))
    else:
        # 非法操作,返回主页
        flash('你没有审核日志的权限')
        return redirect('/')


@main.route('/xJournalEdit', methods=['POST','GET'])
@login_required
def xJournalEdit():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    elif current_user.roleId == 3:
        stuId = request.args.get('stuId')
    else:
        flash("非法操作")
        return redirect("/")    
    jourId = request.args.get('jourId')
    comId = request.args.get('comId')
    internId = request.args.get('internId')
    jour = Journal.query.filter_by(Id=jourId).first()
    student = Student.query.filter_by(stuId=stuId).first()
    comInfor = ComInfor.query.filter_by(comId=comId).first()
    internship = InternshipInfor.query.filter_by(Id=internId).first()
    jourform = journalForm()
    return render_template('xJournalEdit.html', Permission=Permission, jour=jour, student=student, comInfor=comInfor, internship=internship, jourform=jourform)



@main.route('/xJournalEditProcess', methods=['POST','GET'])
@login_required
def xJournalEditProcess():
    if current_user.roleId == 0:
        stuId = current_user.stuId
    elif current_user.roleId == 3:
        stuId = request.form.get('stuId')
    else:
        flash("非法操作")
        return redirect("/")
    jourId = request.form.get('jourId')
    mon = request.form.get('mon')
    tue = request.form.get('tue')
    wed = request.form.get('wed')
    thu = request.form.get('thu')
    fri = request.form.get('fri')
    sat = request.form.get('sat')
    sun = request.form.get('sun')
    stuId = request.form.get('stuId')
    internId = request.form.get('internId')
    try:
        # where加上stuId,是为了防止学生修改其他学生的日志
        db.session.execute('update Journal set \
            mon = "%s", \
            tue = "%s", \
            wed = "%s", \
            thu = "%s", \
            fri = "%s", \
            sat = "%s", \
            sun = "%s" \
            where Id=%s and stuId="%s"'
            % (mon, tue, wed, thu, fri, sat, sun, jourId, stuId))
    except Exception as e:
        print (datetime.now(),": 学号为",stuId,"修改日志失败", e)
        flash("修改日志失败")
        return redirect("/")
    flash("修改日志成功")
    return redirect(url_for('.xJournal', stuId=stuId, internId=internId))


'''
# 学生日志详情
@main.route('/stuJour', methods=['GET'])
@not_student_login
def stuJour():
    comId = request.args.get('comId')
    stuId = request.args.get('stuId')
    student = Student.query.filter_by(stuId=stuId).first()
    com = ComInfor.query.filter_by(comId=comId).first()
    journal = db.session.execute('select * from Journal where stuId=%s and comId=%s' % (stuId, comId))
    return render_template('myjournal.html', Permission=Permission, journal=journal, student=student, com=com)
'''


# 学生用户列表
@main.route('/stuUserList', methods=['GET', 'POST'])
@login_required
def stuUserList():
    # 非管理员,不能进入
    if not current_user.roleId == 3:
        return redirect('/')
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    pagination = Student.query.order_by(Student.grade).paginate(page, per_page=8, error_out=False)
    student = pagination.items
    return render_template('stuUserList.html', pagination=pagination, form=form, Permission=Permission, student=student)


# 添加学生用户
@main.route('/addStudent', methods=['GET', 'POST'])
@login_required
def addStudent():
    # 非管理员,不能进入
    if not current_user.roleId == 3:
        return redirect('/')
    stuform = stuForm()
    if stuform.validate_on_submit():
        stu = Student(
            stuName=stuform.stuName.data,
            stuId=stuform.stuId.data,
            sex=stuform.sex.data,
            institutes=stuform.institutes.data,
            major=stuform.major.data,
            classes=stuform.classes.data,
            grade=stuform.grade.data
        )
        db.session.add(stu)
        try:
            db.session.commit()
            flash('添加学生信息成功！')
            return redirect(url_for('.stuUserList'))
        except Exception as e:
            db.session.rollback()
            flash('添加学生信息失败请重试！')
            print('添加学生信息：', e)
            return redirect(url_for('.addStudent'))
    return render_template('addStudent.html', stuform=stuform, Permission=Permission)


# 教师用户列表
@main.route('/teaUserList', methods=['GET', 'POST'])
@login_required
def teaUserList():
    # 非管理员,不能进入
    if not current_user.roleId == 3:
        return redirect('/')
    form = searchForm()
    page = request.args.get('page', 1, type=int)
    pagination = Teacher.query.order_by(Teacher.teaName).paginate(page, per_page=8, error_out=False)
    teacher = pagination.items
    for tea in teacher:
        session[tea.teaId] = tea.role.roleName
    return render_template('teaUserList.html', pagination=pagination, form=form, Permission=Permission,
                           teacher=teacher)


# 添加教师用户
@main.route('/addTeacher', methods=['GET', 'POST'])
@login_required
def addTeacher():
    # 非管理员,不能进入
    if not current_user.roleId == 3:
        return redirect('/')
    form = teaForm()
    if form.validate_on_submit():
        tea = Teacher(teaName=form.teaName.data, teaId=form.teaId.data, teaSex=form.teaSex.data)
        db.session.add(tea)
        try:
            db.session.commit()
            flash('添加教师信息成功！')
            return redirect(url_for('.teaUserList'))
        except Exception as e:
            db.session.rollback()
            flash('添加教师信息失败请重试！')
            print('添加教师信息：', e)
            return redirect(url_for('.addTeacher'))
    return render_template('addTeacher.html', form=form, Permission=Permission)


# 系统角色列表
@main.route('/roleList', methods=['GET', 'POST'])
@login_required
def roleList():
    # 非管理员,不能进入
    if not current_user.roleId == 3:
        return redirect('/')
    role = Role.query.all()
    return render_template('roleList.html', Permission=Permission, role=role)


# 查询最大的企业Id
def getMaxComId():
    res = db.session.query(func.max(ComInfor.comId).label('max_comId')).one()
    return res.max_comId


# 添加角色,靠你们改善这个蠢方法了,\r\n不能换行，导致角色列表里的describe不能显全
@main.route('/addRole', methods=['GET', 'POST'])
@login_required
def addRole():
    form = permissionForm()
    p = []
    a = 0
    if form.validate_on_submit():
        if form.COM_INFOR_SEARCH.data:
            p.append('企业信息查看\r\n')
            a = eval(form.COM_INFOR_SEARCH.description) | a
        if form.COM_INFOR_EDIT.data:
            a = eval(form.COM_INFOR_EDIT.description) | a
            p.append('企业信息编辑\r\n')
        if form.COM_INFOR_CHECK.data:
            a = eval(form.COM_INFOR_CHECK.description) | a
            p.append('企业信息审核\r\n')
        if form.INTERNSHIP_LIST.data:
            a = eval(form.INTERNSHIP_LIST.description) | a
            p.append('实习企业信息列表\r\n')
        if form.STU_INTERN_LIST.data:
            a = eval(form.STU_INTERN_LIST.description) | a
            p.append('学生实习信息列表\r\n')
        if form.STU_INTERN_SEARCH.data:
            a = eval(form.STU_INTERN_SEARCH.description) | a
            p.append('学生实习信息查看\r\n')
        if form.STU_INTERN_EDIT.data:
            a = eval(form.STU_INTERN_EDIT.description) | a
            p.append('学生实习信息编辑\r\n')
        if form.STU_INTERN_CHECK.data:
            a = eval(form.STU_INTERN_CHECK.description) | a
            p.append('学生实习信息审核\r\n')
        if form.STU_INTERN_EXPORT.data:
            a = eval(form.STU_INTERN_EXPORT.description) | a
            p.append('学生实习信息导出\r\n')
        if form.STU_JOUR_SEARCH.data:
            a = eval(form.STU_JOUR_SEARCH.description) | a
            p.append('学生实习日志查看\r\n')
        if form.STU_JOUR_EDIT.data:
            a = eval(form.STU_JOUR_EDIT.description) | a
            p.append('学生实习日志编辑\r\n')
        if form.STU_JOUR_CHECK.data:
            a = eval(form.STU_JOUR_CHECK.description) | a
            p.append('学生实习日志审核\r\n')
        if form.STU_JOUR_EXPORT.data:
            a = eval(form.STU_JOUR_EXPORT.description) | a
            p.append('学生实习日志导出\r\n')
        if form.STU_SUM_SEARCH.data:
            a = eval(form.STU_SUM_SEARCH.description) | a
            p.append('学生实习总结查看\r\n')
        if form.STU_SUM_EDIT.data:
            a = eval(form.STU_SUM_EDIT.description) | a
            p.append('学生实习总结编辑\r\n')
        if form.STU_SUM_EXPORT.data:
            a = eval(form.STU_SUM_EXPORT.description) | a
            p.append('学生实习总结导出\r\n')
        if form.STU_SUM_CHECK.data:
            a = eval(form.STU_SUM_CHECK.description) | a
            p.append('学生实习总结审核\r\n')
        if form.STU_SCO_SEARCH.data:
            a = eval(form.STU_SCO_SEARCH.description) | a
            p.append('学生实习成果查看\r\n')
        if form.STU_SCO_EDIT.data:
            a = eval(form.STU_SCO_EDIT.description) | a
            p.append('学生实习成果编辑\r\n')
        if form.STU_SCO_EXPORT.data:
            a = eval(form.STU_SCO_EXPORT.description) | a
            p.append('学生实习成果导出\r\n')
        if form.ADMIN.data:
            a = eval(form.ADMIN.description) | a
            p.append('管理\r\n')
        if form.STU_INTERN_IMPORT.data:
            a = eval(form.STU_INTERN_IMPORT.description) | a
            p.append('学生信息导入\r\n')
        if form.TEA_INFOR_IMPORT.data:
            a = eval(form.TEA_INFOR_IMPORT.description) | a
            p.append('老师信息导入\r\n')
        if form.PERMIS_MANAGE.data:
            a = eval(form.PERMIS_MANAGE.description) | a
            p.append('权限管理\r\n')
        per = hex(a)
        print(per)
        describe = ''.join(p)
        print(describe)
        id = getMaxRoleId() + 1
        print(id)
        role = Role(roleName=form.roleName.data, roleDescribe=describe, permission=per, roleId=id)
        try:
            db.session.add(role)
            db.session.commit()
            flash('添加系统角色成功！')
            return redirect(url_for('.roleList'))
        except Exception as e:
            flash('添加系统角色失败！请重试。。。')
            print('添加系统角色：', e)
            db.session.rollback()
            return redirect(url_for('.addRole'))
    return render_template('addRole.html', Permission=Permission, form=form)


# 查询最大的角色Id
def getMaxRoleId():
    res = db.session.query(func.max(Role.roleId).label('max_roleId')).one()
    return res.max_roleId


# 企业信息筛选项，组合查询,当flag=Ture为企业实习信息和批量删除的功能,False为批量审核功能
def create_com_filter(city, flag=True):
    # 更新筛选项
    if request.args.get('city') is not None:
        session['city'] = request.args.get('city')
        print(session['city'])

    if request.args.get('name') is not None:
        session['name'] = request.args.get('name')
        print(session['name'])

    if request.args.get('students') is not None:
        session['students'] = request.args.get('students')
        print(session['students'])

    if request.args.get('status') is not None:
        session['status'] = request.args.get('status')
        print(session['status'])
    i = 0
    # 组合查询 *_*
    try:
        if session.get('city') is not None:
            print('city:', session['city'])
            com = ComInfor.query.filter_by(comAddress=session['city'])

            if session.get('name') is not None:
                if session['name'] == 'desc':
                    com = com.order_by(ComInfor.comName.desc())
                    print('name')
                else:
                    com = com.order_by(ComInfor.comName.asc())
                    print('name')

            if session.get('students') is not None:
                if session['students'] == 'desc':
                    com = com.order_by(ComInfor.students.desc())
                    print('students')
                else:
                    com = com.order_by(ComInfor.students.asc())
                    print('students')

            if session.get('status') is not None:
                if flag:
                    if session['status'] == '2':
                        com = com.filter_by(comCheck=2)
                        print('status')
                    else:
                        com = com.filter(ComInfor.comCheck != 2)
                        print('status')
                else:
                    if session['status'] == '1':
                        com = com.filter_by(comCheck=1)
                        print('status')
                    else:
                        com = com.filter_by(comCheck=0)
                        print('status')
            if flag:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor')
                    print('pagination')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck=2')
        elif session.get('name') is not None:
            if session['name'] == 'desc':
                com = ComInfor.query.order_by(ComInfor.comName.desc())
            else:
                com = ComInfor.query.order_by(ComInfor.comName.asc())
            if session.get('students') is not None:
                if session['students'] == 'desc':
                    com = com.order_by(ComInfor.students.desc())
                else:
                    com = com.order_by(ComInfor.students.asc())
            if session.get('status') is not None:
                if flag:
                    if session['status'] == '2':
                        com = com.filter_by(comCheck=2)
                    else:
                        com = com.filter(ComInfor.comCheck != 2)
                else:
                    if session['status'] == '1':
                        com = com.filter_by(comCheck=1)
                        print('status')
                    else:
                        com = com.filter_by(comCheck=0)
                        print('status')
            if session.get('city') is not None:
                com = com.filter_by(comAddress=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck=2')
        elif session.get('students') is not None:
            if session['students'] == 'desc':
                com = ComInfor.query.order_by(ComInfor.students.desc())
            else:
                com = ComInfor.query.order_by(ComInfor.students.asc())
            if session.get('name') is not None:
                if session['name'] == 'desc':
                    com = com.order_by(ComInfor.comName.desc())
                else:
                    com = com.order_by(ComInfor.comName.asc())
            if session.get('status') is not None:
                if flag:
                    if session['status'] == '2':
                        com = com.filter_by(comCheck=2)
                    else:
                        com = com.filter(ComInfor.comCheck != 2)
                else:
                    if session['status'] == '1':
                        com = com.filter_by(comCheck=1)
                        print('status')
                    else:
                        com = com.filter_by(comCheck=0)
                        print('status')
            if session.get('city') is not None:
                com = com.filter_by(comAddress=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck=2')
        elif session.get('status') is not None:
            if flag:
                if session['status'] == '2':
                    com = ComInfor.query.filter_by(comCheck=2)
                else:
                    com = ComInfor.query.filter(ComInfor.comCheck != 2)
            else:
                if session['status'] == '1':
                    com = ComInfor.query.filter_by(comCheck=1)
                    print('status')
                else:
                    com = ComInfor.query.filter_by(comCheck=0)
                    print('status')

            if session.get('name') is not None:
                if session['name'] == 'desc':
                    com = com.order_by(ComInfor.comName.desc())
                else:
                    com = com.order_by(ComInfor.comName.asc())
            if session.get('students') is not None:
                if session['students'] == 'desc':
                    com = com.order_by(ComInfor.students.desc())
                else:
                    com = com.order_by(ComInfor.students.asc())
            if session.get('city') is not None:
                com = com.filter_by(comAddress=session['city'])

            if flag:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor')
                else:
                    com = com.filter_by(comCheck=2)
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck=2')
        else:
            if flag:
                if current_user.can(Permission.COM_INFOR_CHECK):
                    com = ComInfor.query.order_by(ComInfor.comDate.desc())
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor')
                    print('hi')
                else:
                    com = ComInfor.query.filter_by(comCheck=2).order_by(ComInfor.comDate.desc())
                    citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck=2')
            else:
                com = ComInfor.query.filter(ComInfor.comCheck != 2).order_by(ComInfor.comDate.desc())
                citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck!=2')
        if not flag:
            com = com.filter(ComInfor.comCheck != 2)
            citys = db.session.execute('select DISTINCT comAddress from ComInfor WHERE comCheck!=2')
    except Exception as e:
        print('组合筛选：', e)
    # 生成筛选项
    for c in citys:
        city[i] = c.comAddress
        i = i + 1
    return com
