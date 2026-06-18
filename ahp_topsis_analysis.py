import pandas as pd
import numpy as np

def run_analysis():
    print("1. Veri seti yükleniyor...")
    # Veri setini (amazon.csv) yükle
    try:
        raw_df = pd.read_csv('amazon.csv')
    except FileNotFoundError:
        print("Hata: 'amazon.csv' dosyası bulunamadı! Lütfen dosyanın bu klasörde olduğundan emin olun.")
        return

    print("2. Veriler temizleniyor ve dönüştürülüyor...")
    # Fiyat kolonlarındaki '₹' ve ',' işaretlerini kaldırıp float'a çevir
    raw_df['discounted_price'] = raw_df['discounted_price'].astype(str).str.replace('₹', '').str.replace(',', '').astype(float)
    raw_df['actual_price'] = raw_df['actual_price'].astype(str).str.replace('₹', '').str.replace(',', '').astype(float)

    # İndirim yüzdesindeki '%' işaretini kaldırıp float'a çevir
    raw_df['discount_percentage'] = raw_df['discount_percentage'].astype(str).str.replace('%', '').astype(float)

    # Puan ve puan sayısı kolonlarını sayısal formata çevir
    raw_df['rating'] = pd.to_numeric(raw_df['rating'].astype(str).str.replace(',', '.'), errors='coerce')
    raw_df['rating_count'] = pd.to_numeric(raw_df['rating_count'].astype(str).str.replace(',', ''), errors='coerce')

    # Eksik verileri temizle
    clean_df = raw_df.dropna(subset=['rating', 'rating_count', 'discount_percentage', 'discounted_price', 'actual_price']).copy()

    # Orijinal notebook değişken isimlerine eşle (AHP-TOPSIS analizi için)
    df = pd.DataFrame()
    df['Alternatif'] = ['A' + str(i+1) for i in range(len(clean_df))]
    df['Urun'] = clean_df['product_name'].values
    df['Rating'] = clean_df['rating'].values
    df['Rating_Count'] = clean_df['rating_count'].values
    df['Discount'] = clean_df['discount_percentage'].values
    df['Discounted_Price'] = clean_df['discounted_price'].values
    df['Actual_Price'] = clean_df['actual_price'].values

    print(f"Toplam {len(df)} ürün başarıyla yüklendi ve temizlendi.")

    # AHP sonucunda elde edilen kriter ağırlıkları
    # Sırasıyla: Rating, Rating_Count, Discount, Discounted_Price, Actual_Price
    weights = np.array([0.48, 0.26, 0.13, 0.08, 0.05])

    # TOPSIS analizinde kullanılacak kriter sütunları
    criteria = ["Rating", "Rating_Count", "Discount", "Discounted_Price", "Actual_Price"]

    # Karar matrisi
    X = df[criteria].values.astype(float)

    # Vektör normalizasyonu
    norms = np.sqrt((X ** 2).sum(axis=0))
    # Sıfıra bölme hatasını engellemek için kontrol
    norms[norms == 0] = 1e-9
    normalized_matrix = X / norms

    # AHP ağırlıkları ile normalize karar matrisinin çarpılması
    weighted_matrix = normalized_matrix * weights

    # Fayda kriterleri indeksleri: Rating (0), Rating Count (1), Discount (2)
    # Maliyet kriterleri indeksleri: Discounted Price (3), Actual Price (4)
    benefit_criteria = [0, 1, 2]
    cost_criteria = [3, 4]

    positive_ideal = np.zeros(weighted_matrix.shape[1])
    negative_ideal = np.zeros(weighted_matrix.shape[1])

    for i in range(weighted_matrix.shape[1]):
        if i in benefit_criteria:
            positive_ideal[i] = weighted_matrix[:, i].max()
            negative_ideal[i] = weighted_matrix[:, i].min()
        else:
            positive_ideal[i] = weighted_matrix[:, i].min()
            negative_ideal[i] = weighted_matrix[:, i].max()

    # Uzaklık hesapları
    distance_positive = np.sqrt(((weighted_matrix - positive_ideal) ** 2).sum(axis=1))
    distance_negative = np.sqrt(((weighted_matrix - negative_ideal) ** 2).sum(axis=1))

    # TOPSIS skoru
    topsis_score = distance_negative / (distance_positive + distance_negative)

    results = df[["Alternatif", "Urun", "Rating", "Discounted_Price"]].copy()
    results["TOPSIS_Skoru"] = topsis_score
    results["Siralama"] = results["TOPSIS_Skoru"].rank(ascending=False).astype(int)

    results = results.sort_values("Siralama")

    print("\n--- TOPSIS Sonuçları (En İyi 15 Ürün) ---")
    print(results.head(15).to_string(index=False))

    # Sonuçları yeni bir csv dosyası olarak kaydet
    results.to_csv('topsis_sonuclari.csv', index=False, encoding='utf-8-sig')
    print("\nTüm sonuçlar 'topsis_sonuclari.csv' olarak kaydedildi.")

if __name__ == "__main__":
    run_analysis()
