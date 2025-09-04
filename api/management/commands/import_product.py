import csv
from decimal import Decimal
from django.core.exceptions import ValidationError
from api.models import Product 

file_path = "Charms Data For Database - Product.csv" 

with open(file_path, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        try:
            # Bersihkan & mapping data
            name = row.get("name", "").strip()
            category = row.get("category", "").strip().lower()
            label = row.get("label", "null").strip().lower()
            price = Decimal(row.get("price", "0").strip() or "0")
            rating = Decimal(row.get("rating", "0").strip() or "0")
            description = row.get("description", "").strip() or None
            details = row.get("details", "").strip() or None
            stock = int(row.get("stock", "0").strip() or 0)
            sold_stok = int(row.get("sold_stok", "0").strip() or 0)
            discount = Decimal(row.get("discount", "0").strip() or "0")
            charms = row.get("charms", "False").strip().lower() in ["1", "true", "yes"]
            is_charm_spreadable = row.get("is_charm_spreadable", "False").strip().lower() in ["1", "true", "yes"]

            # Buat object
            product = Product(
                name=name,
                category=category,
                label=label,
                price=price,
                rating=rating,
                description=description,
                details=details,
                stock=stock,
                sold_stok=sold_stok,
                discount=discount,
                charms=charms,
                is_charm_spreadable=is_charm_spreadable,
            )

            # Validasi model (jalankan clean())
            product.full_clean()
            product.save()
            print(f"✅ Berhasil tambah produk: {name}")

        except ValidationError as e:
            print(f"❌ Validation error pada produk {row.get('name')}: {e}")
        except Exception as e:
            print(f"⚠️ Gagal tambah produk {row.get('name')}: {e}")
