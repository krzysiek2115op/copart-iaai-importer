"""
Copart — SZKIELET (NIE uruchamiać produkcyjnie bez zgody prawnej).

⚠️⚠️⚠️  OSTRZEŻENIE  ⚠️⚠️⚠️
copart.com jest w całości chroniony przez Imperva Incapsula (agresywny tryb:
JS challenge na każdym żądaniu anonimowym). Pobieranie danych przez automatyczne
przechodzenie tego challenge to OMIJANIE ZABEZPIECZEŃ — sprzeczne z ToS Copart
i potencjalnie z prawem (np. CFAA w USA). Ten plik jest wyłącznie szkieletem
poglądowym; w projekcie REKOMENDUJEMY drogi legalne (patrz report.md §3):
  1) licencjonowane API third-party (Copart+IAAI),
  2) oficjalny eksport CSV "Sales Data" z konta członkowskiego Copart.

Poniższy kod NIE jest kompletną implementacją obejścia i celowo go nie dostarcza.
"""
from __future__ import annotations

LEGAL_OPTIONS = """
Legalne źródła danych Copart:
  - CSV Sales Data (po zalogowaniu):
        https://www.copart.com/content/us/en/buyer/sales/download-sales-data
  - Licencjonowane API third-party (Copart + IAAI):
        auction-api.app, auctionsapi.com, apiauctions.io, carstat.dev, apibara.tech

Endpointy front-endu (istnieją, ale za Incapsula — dostęp tylko z ważną sesją
zalogowanego członka, zgodnie z ToS):
  GET  https://www.copart.com/public/data/lotdetails/solr/{lotNumber}
  POST https://www.copart.com/public/lots/search-results
"""


def main():
    print(LEGAL_OPTIONS)
    print("Aby pozyskać dane Copart zgodnie z prawem, wybierz jedną z dróg powyżej.")


if __name__ == "__main__":
    main()
