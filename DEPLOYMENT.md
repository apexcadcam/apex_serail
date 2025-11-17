# 🚀 دليل النشر - Apex Serial App

هذا الدليل يوضح كيفية نشر `apex_serial` على سيرفر خارجي بدون أي تعديلات على Frappe core.

## ✅ المتطلبات

### 1. متطلبات Frappe Bench القياسية
- Python 3.10+
- MariaDB/MySQL
- Redis (Cache + Queue)
- Node.js 18+
- Frappe Framework

### 2. تثبيت التطبيق

```bash
# على السيرفر الخارجي
cd /path/to/frappe-bench

# الحصول على التطبيق من GitHub
bench get-app apex_serial https://github.com/apexcadcam/apex_serail.git

# تثبيت التطبيق على الموقع
bench --site your-site.com install-app apex_serial

# إعادة بناء Assets
bench build --app apex_serial

# إعادة تشغيل الخادم
bench restart
```

## ⚠️ ملاحظات مهمة

### 1. مجلد Translations
التطبيق يحتوي على مجلد `translations/` فارغ. هذا ضروري لتعمل التطبيق بشكل صحيح.

**لا تقم بحذف هذا المجلد!**

### 2. Frappe Core
**لا تحتاج أي تعديلات على Frappe core!**

التطبيق يعمل بشكل كامل بدون تعديلات على:
- `frappe/translate.py`
- `frappe/model/sync.py`

إذا واجهت مشكلة `ModuleNotFoundError: No module named 'apex_serial'`:

#### الحل السريع:
```bash
# تأكد من أن التطبيق مثبت بشكل صحيح
bench --site your-site.com migrate

# تأكد من أن apex_serial موجود في apps.txt
cat sites/your-site.com/apps.txt | grep apex_serial

# إذا لم يكن موجود، أضفه:
echo "apex_serial" >> sites/your-site.com/apps.txt

# أعد بناء Assets
bench build --app apex_serial

# أعد تشغيل الخادم
bench restart
```

### 3. Python Package Installation
التطبيق يجب أن يكون مثبت كـ Python package:

```bash
cd /path/to/frappe-bench
pip install -e apps/apex_serial
```

هذا يتم تلقائياً عند `bench get-app` أو `bench install-app`.

## 🔧 التحقق من التثبيت

### 1. التحقق من Custom Fields
```bash
bench --site your-site.com console
```

```python
import frappe

# التحقق من وجود Custom Fields
fields = frappe.get_all(
    "Custom Field",
    filters={"dt": "Serial No", "module": "Apex Serial"},
    fields=["name", "fieldname"]
)

print(f"Found {len(fields)} Apex Serial custom fields")
for f in fields:
    print(f"  - {f.fieldname}")

# يجب أن تكون 8 fields:
# apx_is_used, apx_is_demo, apx_last_stock_entry,
# apx_last_transfer_reason, apx_demo_owner_type,
# apx_demo_owner, apx_demo_expected_return, apx_previous_warehouse
```

### 2. التحقق من JavaScript
افتح Serial No form وتحقق من وجود الأزرار:
- "Mark as Used"
- "Send as Demo"
- "Receive Demo"

### 3. التحقق من Python Methods
```python
import frappe
from apex_serial.serial_flow import mark_serial_as_used

# التحقق من أن الدوال متاحة
print("✅ Apex Serial installed correctly")
```

## 📋 Custom Fields المثبتة

التطبيق يثبت 8 Custom Fields على Serial No:

1. `apx_is_used` - Boolean (Is Used)
2. `apx_is_demo` - Boolean (Is Demo)
3. `apx_last_stock_entry` - Link (Last Stock Entry)
4. `apx_last_transfer_reason` - Data (Last Transfer Reason)
5. `apx_demo_owner_type` - Select (Demo Owner Type)
6. `apx_demo_owner` - Dynamic Link (Demo Owner)
7. `apx_demo_expected_return` - Date (Expected Return Date)
8. `apx_previous_warehouse` - Link (Previous Warehouse)

## 🗑️ إلغاء التثبيت

```bash
bench --site your-site.com uninstall-app apex_serial
```

هذا سيحذف:
- ✅ جميع 8 Custom Fields
- ✅ Module Definition
- ⚠️ Warehouses ستبقى (بيانات مستخدم)

## ❓ حل المشاكل الشائعة

### Problem 1: ModuleNotFoundError: No module named 'apex_serial'
**الحل:**
```bash
pip install -e apps/apex_serial
bench --site your-site.com migrate
bench build --app apex_serial
bench restart
```

### Problem 2: Custom Fields لا تظهر
**الحل:**
```bash
bench --site your-site.com migrate
bench --site your-site.com clear-cache
bench restart
```

### Problem 3: JavaScript buttons لا تظهر
**الحل:**
```bash
bench build --app apex_serial
bench --site your-site.com clear-cache
# Hard refresh في المتصفح (Ctrl+Shift+R)
```

## 📝 ملاحظات

- التطبيق مستقل تماماً ولا يحتاج أي تعديلات على Frappe core
- جميع التبعيات موثقة في `pyproject.toml`
- التطبيق متوافق مع Frappe v15+
- التطبيق متوافق مع ERPNext v15+

## 🔗 روابط مفيدة

- GitHub Repository: https://github.com/apexcadcam/apex_serail
- Frappe Documentation: https://frappeframework.com/docs
- ERPNext Documentation: https://docs.erpnext.com

