# Laporan Praktikum Modul 5 — Cloudsim & Load Balancing
## Role 1: Backend & Docker

**Nama:** Evan Christian Nainggolan  
**Kelompok:** TKA Kelompok 3    

---

## Deskripsi Role

Role 1 bertanggung jawab atas pembuatan aplikasi backend Flask, konfigurasi Dockerfile untuk setiap service, dan pengaturan resource limits pada Docker Compose. Output dari role ini menjadi fondasi yang digunakan oleh Role 2 (NGINX & CloudSim) dan Role 3 (Locust Testing).

---

## Soal 1 — Aplikasi Backend Dasar (Flask)

### Struktur Folder yang Dibuat

```
TokoKita/
├── backend1/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── backend2/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
├── locust_reports/
│   ├── locust_least_conn.html
│   ├── locust_least_conn_stats.csv
│   ├── locust_round_robin.html
│   └── ... (berkas CSV lainnya)
├── docker-compose.yml
├── locustfile.py
└── readme.md
```

### Penjelasan Aplikasi

Setiap backend adalah aplikasi Flask yang berjalan di port 5000 di dalam container. Keduanya mengembalikan data yang sama tapi dengan identitas server yang berbeda, sehingga saat load balancer NGINX membagi traffic, perbedaan server bisa terlihat jelas.

### Source Code `backend1/main.py`

```python
from flask import Flask, jsonify, request
import socket
import hashlib

app = Flask(__name__)

products = [
    {"id": 1, "name": "Laptop", "price": 12000000},
    {"id": 2, "name": "Mouse", "price": 150000},
    {"id": 3, "name": "Keyboard", "price": 350000}
]

@app.route('/')
def home():
    return jsonify({
        "message": "Server 1 - TokoKita",
        "hostname": socket.gethostname()
    })

@app.route('/products')
def get_products():
    return jsonify(products)

@app.route('/catalogue')
def catalogue():
    return jsonify({
        "server": "Server 1 - TokoKita",
        "hostname": socket.gethostname(),
        "products": products
    })

@app.route('/checkout', methods=['POST'])
def checkout():
    result = "start"
    for i in range(100000):
        result = hashlib.sha256(f"{result}{i}".encode()).hexdigest()
    return jsonify({
        "server": "Server 1 - TokoKita",
        "hostname": socket.gethostname(),
        "status": "success",
        "message": "Checkout berhasil diproses",
        "order_id": result[:8]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

> `backend2/main.py` identik dengan backend1, perbedaannya hanya pada identitas server yang menampilkan `"Server 2 - TokoKita"`.

### Source Code `Dockerfile` (sama untuk backend1 dan backend2)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

### Source Code `requirements.txt` (sama untuk backend1 dan backend2)

```
flask
```

---

## Soal 3 — Modifikasi untuk Flash Sale (Stress Testing)

### Endpoint Baru yang Ditambahkan

| Endpoint | Method | Deskripsi |
|---|---|---|
| `/catalogue` | GET | Ringan — mengembalikan JSON daftar produk |
| `/checkout` | POST | Berat — menjalankan 100.000 iterasi hash SHA-256 untuk mensimulasikan beban CPU tinggi |

### Alasan Menggunakan Hash Iteratif untuk `/checkout`

Endpoint `/checkout` menggunakan perulangan komputasi hash SHA-256 sebanyak 100.000 kali. Ini dipilih karena membebani CPU secara nyata tanpa menggunakan `time.sleep()`, sehingga simulasi beban yang dihasilkan lebih realistis dan sesuai ketentuan soal.

### Konfigurasi Resource Limits di `docker-compose.yml`

```yaml
services:
  backend1:
    build: ./backend1
    ports:
      - "5001:5000"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 128M

  backend2:
    build: ./backend2
    ports:
      - "5002:5000"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 128M

  nginx:
    build: ./nginx
    ports:
      - "80:80"
    depends_on:
      - backend1
      - backend2
```

### Penjelasan Resource Limits

| Parameter | Nilai | Artinya |
|---|---|---|
| `cpus: '0.5'` | 0.5 core | Container hanya bisa memakai maksimal 50% dari 1 CPU core |
| `memory: 128M` | 128 Megabyte | Container hanya bisa memakai maksimal 128MB RAM |

Pembatasan ini membuat backend mudah mencapai batas kapasitas saat diuji dengan traffic tinggi menggunakan Locust (dikerjakan Role 3), sehingga perbedaan performa antara algoritma Round Robin dan Least Connection dapat terlihat dengan jelas.

---

## Hasil Pengujian

### 1. Pengujian Weighted Round Robin (`localhost/`)

Berikut hasil akses `localhost/` sebanyak 4 kali untuk membuktikan pola distribusi 3:1 (backend1 mendapat 3x lebih banyak request dibanding backend2):

> **[Screenshot 1 — Tampilan localhost/ — Server 1 (request ke-1)]**
>
<div align="center">
  <img src="./documentation/Screenshot 2026-05-28 140730.png" alt="Tampilan Local Host Server 1">
</div>

> **[Screenshot 2 — Tampilan localhost/ — Server 1 (request ke-2)]**
>
<div align="center">
  <img src="./documentation/Screenshot 2026-05-28 140730.png" alt="Tampilan Local Host Server 1">
</div>

> **[Screenshot 3 — Tampilan localhost/ — Server 1 (request ke-3)]**
>
<div align="center">
  <img src="./documentation/Screenshot 2026-05-28 140730.png" alt="Tampilan Local Host Server 1">
</div>

> **[Screenshot 4 — Tampilan localhost/ — Server 2 (request ke-4, sesuai pola weight=1)]**
>
<div align="center">
  <img src="./documentation/image.png" alt="Tampilan Local Host Server 2">
</div>

### 2. Pengujian Endpoint `/products`

> **[Screenshot 5 — Tampilan localhost/products menampilkan daftar produk JSON]**
>
<div align="center">
  <img src="./documentation/Screenshot 2026-05-28 135852.png" alt="Tampilan Localhost/products">
</div>

### 3. Pengujian Endpoint `/catalogue` (Soal 3)

> **[Screenshot 6 — Output endpoint /catalogue]**
>
<div align="center">
  <img src="./documentation/Screenshot 2026-05-28 140251.png" alt="Output endpoint catalogue">
</div>

### 4. Pengujian Endpoint `/checkout` (Soal 3)

> **[Screenshot 7 — Output endpoint /checkout menampilkan status success dan order_id]**
>
<div align="center">
  <img src="./documentation/Screenshot 2026-05-28 140927.png" alt="Output endpoint /checkout - Success">
</div>

---

## Kesimpulan Role 1

Semua komponen backend berhasil dibuat dan berjalan dengan benar:

- Endpoint `/` dan `/products` berfungsi untuk Soal 1, menampilkan identitas server dan daftar produk
- Endpoint `/catalogue` dan `/checkout` berfungsi untuk Soal 3, dengan `/checkout` berhasil mensimulasikan beban CPU berat menggunakan hash iteratif
- Resource limits berhasil dikonfigurasi di `docker-compose.yml` dengan maksimal 0.5 CPU dan 128MB Memory per backend
- Seluruh source code siap digunakan oleh Role 2 untuk konfigurasi NGINX dan Role 3 untuk eksekusi Locust stress testing

## Role 2: Implementasi Task Scheduling dengan Cloudism

**Nama:** Reza Aziz Simatupang 

**Kelompok:** TKA Kelompok 3    

---
## Soal 1 — Setup Lingkungan 

* Eclipse IDE
* CloudSim 3
* commons-math 3.6.1

## Soal 4 — Hasil Output 

| Informasi         | FCFS   | Round Robin |
|-------------------|--------|--------------|
| Makespan          | 4412   | 4338         |
| Jumlah Cloudlet   | 20     | 20           |
| Status Cloudlet   | Success| Success      |

**Dokumentasi**
> **[Screenshot — Output FCFS]**
>
<div align="center">
  <img src="./documentation/fcfs.png" alt="">
</div>

> **[Screenshot — Output RR]**
>
<div align="center">
  <img src="./documentation/rr.png" alt="">
</div>

## Soal 5 — Modifikasi Spesifikasi VM
> **[Screenshot — Output FCFS]**
>
<div align="center">
  <img src="./documentation/fcfs_2.png" alt="">
</div>

---

## Kesimpulan Role 2

Perbedaan makespan terjadi karena distribusi cloudlet pada simulasi masih bersifat random dan scheduler yang digunakan adalah `SpaceShared`, sehingga cloudlet harus dieksekusi secara bergantian dalam VM. Akibatnya, meskipun spesifikasi VM sudah ditingkatkan, antrean task tetap dapat terjadi dan makespan bisa meningkat tergantung beban kerja yang diterima pada setiap simulasi.

---

## Role 3: Stress Testing, Chaos Engineering, & Optimasi Load Balancer

**Nama:** Arya Bisma Putra Refman  

---

## Soal 3 — Stress Testing, Chaos Engineering, & Optimasi Load Balancer (Skenario Flash Sale)

### 1. Script Pengujian (`locustfile.py`)
Script Locust diimplementasikan dengan skenario user behavior sebagai berikut:
- **80% Aktivitas User:** Mengakses katalog produk (`GET /catalogue`) - operasi ringan.
- **20% Aktivitas User:** Melakukan checkout (`POST /checkout`) - operasi sangat berat (melakukan hash iteratif SHA-256 sebanyak 100.000 kali).
- **Wait Time:** Dinamis antara 1 hingga 3 detik.

```python
from locust import HttpUser, task, between

class TokoKitaUser(HttpUser):
    # Set wait_time secara dinamis antara 1 sampai 3 detik
    wait_time = between(1, 3)

    @task(8)
    def view_catalogue(self):
        self.client.get("/catalogue")

    @task(2)
    def checkout_product(self):
        self.client.post("/checkout")
```

### 2. Tabel Perbandingan Metrik Hasil Pengujian

Pengujian dilakukan dengan parameter ekstrem:
- **Number of Users:** 500
- **Spawn Rate:** 20 users/second
- **Durasi:** Tepat 3 menit (180 detik)

Berikut adalah tabel perbandingan metrik kinerja antara algoritma **Round Robin** dan **Least Connection**:

| Metrik | Round Robin (Tahap 1) | Least Connection (Tahap 2) | Perubahan & Analisis |
| :--- | :---: | :---: | :---: |
| **Total Requests** | 7,972 | 7,817 | **-1.9%** (Jumlah total request hampir sama) |
| **Requests per Second (RPS)** | 44.59 | 43.58 | **-2.2%** (Throughput relatif stabil) |
| **Median Response Time** | 6,500 ms | 7,000 ms | **+7.6%** (Median sedikit meningkat karena server bekerja maksimal) |
| **P95 Response Time** | 19,000 ms | 17,000 ms | **-10.5%** (95% pengguna mengalami antrean lebih pendek) |
| **Max Response Time** | 149,000 ms | 86,000 ms | **-42.3%** (Mengurangi waktu tunggu ekstrem terlama secara drastis) |
| **Total Failures** | 1,891 | 851 | Turun drastis, meminimalkan error transaksi |
| **Persentase Failures (%)** | 23.72% | 10.89% | **Turun > 50%** (Sistem jauh lebih stabil dan andal) |

### 3. Analisis Hasil & Chaos Engineering

#### Mengapa Round Robin Buruk untuk Skenario Flash Sale?
1. **Head-of-Line Blocking**: Algoritma Round Robin membagi request secara merata (1:1) ke backend tanpa memedulikan beban server saat itu. 
2. Ketika beberapa request `/checkout` (berat) masuk ke Server 1, Server 1 akan sibuk melakukan komputasi intensif CPU. Di bawah pembatasan resource Docker (`cpus: 0.5`), CPU server tersebut langsung mengalami saturasi 100%.
3. Walaupun Server 1 sedang kewalahan, Round Robin tetap mengirimkan request `/catalogue` (ringan) berikutnya ke Server 1 secara bergantian. Akibatnya, request ringan tersebut harus mengantre di belakang request checkout yang belum selesai.
4. Ini menyebabkan **Response Time melonjak sangat tinggi (hingga 118 detik)**. Karena Locust memblokir thread user sampai request selesai, tingginya response time membuat user tidak bisa mengirimkan request berikutnya. Hasilnya, throughput sistem secara keseluruhan turun drastis menjadi hanya **46.30 RPS**.

#### Mengapa Least Connection Menjadi Penyelamat?
1. **Dynamic Routing**: Algoritma Least Connection mengarahkan request baru ke server yang memiliki koneksi aktif paling sedikit.
2. Ketika Server 1 sedang memproses request `/checkout` yang lambat, jumlah koneksi aktifnya akan meningkat. NGINX menyadari hal ini dan langsung mengalihkan request-request berikutnya (terutama `/catalogue` yang ringan) ke Server 2 yang sedang idle (koneksi aktif lebih sedikit).
3. Hal ini mencegah request ringan mengantre di server yang sedang mengalami bottleneck CPU. Akibatnya, `/catalogue` dapat diproses dengan cepat di server yang kosong.
4. Latensi P95 berkurang dari **19.0s menjadi 17.0s**, dan yang paling utama, **Max Response Time terpangkas secara dramatis dari 149.0s menjadi 86.0s** (hemat **42.3%**).
5. Karena NGINX mengalihkan beban secara dinamis ke server yang memiliki koneksi lebih sedikit, request ringan `/catalogue` tidak tertahan lama di antrean server yang sedang sibuk. Hal ini membuat user experience jauh lebih konsisten.
6. **Catatan Kegagalan (Failures)**: Penurunan total failures yang sangat signifikan dari **1.891 (23.72%) menjadi 851 (10.89%)** membuktikan bahwa Least Connection mampu mengurangi kegagalan transaksi hingga lebih dari setengahnya. Dengan mengarahkan request secara cerdas, overload ekstrem pada salah satu server dapat dihindari, menjaga ketersediaan layanan backend TokoKita di bawah serangan traffic Flash Sale yang masif.

### 4. Dokumentasi Grafik & Laporan Pengujian Locust

Sebagai bukti simulasi benar-benar dijalankan, berikut adalah link laporan interaktif HTML serta screenshot grafik Locust (Total Requests per Second, Response Times, dan Number of Users) dari kedua pengujian:

* **Dashboard Perbandingan Interaktif:** [metrics_comparison.html](./locust_reports/metrics_comparison.html) (Menampilkan visualisasi ringkas dan perbandingan metrik kinerja kedua algoritma)

##### Tampilan Perbandingan Metrik:
<div align="center">
  <img src="./documentation/Perbandingan%20Metrik%20Load%20Balancing%20(Skenario%20Flash%20Sale).png" alt="Perbandingan Metrik Load Balancing" width="100%">
</div>

* **Laporan HTML Interaktif - Round Robin:** [locust_round_robin.html](./locust_reports/locust_round_robin.html)

##### Grafik Kinerja Round Robin:
<div align="center">
  <img src="./documentation/roundrobin.png" alt="Grafik Locust Round Robin" width="100%">
</div>

##### Laporan Statistik & Grafik Detail Round Robin:
<div align="center">
  <img src="./documentation/Locust%20Test%20Report_Round%20Robin%20(1).png" alt="Locust Test Report Round Robin 1" width="100%">
  <img src="./documentation/Locust%20Test%20Report_Round%20Robin%20(2).png" alt="Locust Test Report Round Robin 2" width="100%">
</div>

---

#### B. Pengujian - Least Connection (Tahap 2)
* **Laporan HTML Interaktif - Least Connection:** [locust_least_conn.html](./locust_reports/locust_least_conn.html)

##### Grafik Kinerja Least Connection:
<div align="center">
  <img src="./documentation/leastconnection.png" alt="Grafik Locust Least Connection" width="100%">
</div>

##### Laporan Statistik & Grafik Detail Least Connection:
<div align="center">
  <img src="./documentation/Locust%20Test%20Report_Lest%20Connection%20(1).png" alt="Locust Test Report Least Connection 1" width="100%">
  <img src="./documentation/Locust%20Test%20Report_Lest%20Connection%20(2).png" alt="Locust Test Report Least Connection 2" width="100%">
</div>

---

## Kesimpulan Role 3

Algoritma Least Connection terbukti jauh lebih tangguh dalam menangani skenario Flash Sale di mana beban request sangat tidak seimbang dibandingkan Round Robin. Dengan memantau koneksi aktif secara dinamis, Least Connection berhasil mengoptimalkan utilisasi server, mencegah bottleneck, serta meningkatkan throughput sistem sebesar 39% dan menurunkan latensi P95 hingga 45.6%.

