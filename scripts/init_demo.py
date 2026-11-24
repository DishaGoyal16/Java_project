"""Provision only the explicitly selected, separate local demo SQLite database."""
import os
import secrets
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code/backend'))
from sqlmodel import Session, select
from app.core.database import engine, create_db_and_tables
from app.core.security import hash_password
from app.models import User, Student, Equipment, Slot, FairnessConfig, UsageStatistics
from app.models.enums import UserRole

expected=(Path(__file__).resolve().parents[1]/'.local/demo.db').as_posix()
if os.getenv('SCMS_DEMO_DATABASE')!='1' or os.environ.get('DATABASE_URL')!='sqlite:///'+expected:
    raise SystemExit('Refusing to seed anything except the isolated .local/demo.db')
password=os.environ['SCMS_DEMO_PASSWORD']
if len(password)<8:raise SystemExit('Demo password must contain at least eight characters')
create_db_and_tables()
with Session(engine) as session:
    for name,email,role in [('Demo Admin','admin@example.com',UserRole.ADMIN),('Demo Staff','staff@example.com',UserRole.STAFF)]:
        if not session.exec(select(User).where(User.email==email)).first():
            session.add(User(name=name,email=email,password_hash=hash_password(password),role=role))
    session.commit()
    admin=session.exec(select(User).where(User.email=='admin@example.com')).first()
    if not session.exec(select(Student).where(Student.email=='student@example.com')).first():
        student=Student(name='Demo Student',student_id='DEMO001',email='student@example.com',department='Computer Science',password_hash=hash_password(password),qr_identifier=secrets.token_urlsafe(32))
        session.add(student);session.commit();session.refresh(student)
        session.add(UsageStatistics(student_id=student.id))
    if not session.get(FairnessConfig,1):session.add(FairnessConfig())
    session.commit()
    tomorrow=(datetime.now(timezone.utc)+timedelta(days=1)).date()
    for i,name in enumerate(['Cricket Bat','Football','Basketball','Badminton Racket']):
        item=session.exec(select(Equipment).where(Equipment.qr_code==f'DEMO-EQ-{i}')).first()
        if item is None:
            item=Equipment(name=name,category=name.split()[0],qr_code=f'DEMO-EQ-{i}',added_by=admin.id,location='Sports Room')
            session.add(item);session.commit();session.refresh(item)
        if not session.exec(select(Slot).where(Slot.equipment_id==item.id,Slot.date==tomorrow)).first():
            session.add(Slot(equipment_id=item.id,date=tomorrow,start_time=time(9),end_time=time(10),capacity=1,available_count=1,booking_cutoff_at=datetime.now(timezone.utc)+timedelta(hours=1),created_by=admin.id))
    session.commit()
print('Separate demo database ready. Accounts: admin@example.com, staff@example.com, student@example.com.')
print('Existing accounts keep their password. No production database was seeded.')
