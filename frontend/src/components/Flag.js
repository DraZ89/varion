// ========== FLAG COMPONENT - flag-icons (lipis/flag-icons via jsDelivr) ==========
// SVG vectoriels qualite production, 250+ pays
// CDN : https://cdn.jsdelivr.net/gh/lipis/flag-icons/flags/4x3/{iso2}.svg

// Mapping ATP/WTA 3-lettres -> ISO 2-lettres
// Liste exhaustive ATP/WTA + JO + Coupe Davis
const COUNTRY_3_TO_2 = {
  // Europe
  ALB: "AL", AND: "AD", ARM: "AM", AUT: "AT", AZE: "AZ", BEL: "BE", BIH: "BA",
  BLR: "BY", BUL: "BG", CRO: "HR", CYP: "CY", CZE: "CZ", DEN: "DK", ESP: "ES",
  EST: "EE", FIN: "FI", FRA: "FR", GBR: "GB", GEO: "GE", GER: "DE", GRE: "GR",
  HUN: "HU", IRL: "IE", ISL: "IS", ITA: "IT", LAT: "LV", LIE: "LI", LTU: "LT",
  LUX: "LU", MDA: "MD", MKD: "MK", MLT: "MT", MNE: "ME", MON: "MC", NED: "NL",
  NOR: "NO", POL: "PL", POR: "PT", ROU: "RO", RUS: "RU", SMR: "SM", SRB: "RS",
  SUI: "CH", SVK: "SK", SVN: "SI", SWE: "SE", TUR: "TR", UKR: "UA", VAT: "VA",
  // Ameriques
  ARG: "AR", BAH: "BS", BAR: "BB", BOL: "BO", BRA: "BR", CAN: "CA", CHI: "CL",
  COL: "CO", CRC: "CR", CUB: "CU", DOM: "DO", ECU: "EC", ESA: "SV", GUA: "GT",
  HAI: "HT", HON: "HN", JAM: "JM", MEX: "MX", NCA: "NI", PAN: "PA", PAR: "PY",
  PER: "PE", PUR: "PR", URU: "UY", USA: "US", VEN: "VE",
  // Asie
  CHN: "CN", HKG: "HK", IND: "IN", INA: "ID", IRI: "IR", IRQ: "IQ", ISR: "IL",
  JOR: "JO", JPN: "JP", KAZ: "KZ", KGZ: "KG", KOR: "KR", KSA: "SA", KUW: "KW",
  LBN: "LB", MAS: "MY", MGL: "MN", PAK: "PK", PHI: "PH", QAT: "QA", SGP: "SG",
  SRI: "LK", SYR: "SY", THA: "TH", TJK: "TJ", TKM: "TM", TPE: "TW", UAE: "AE",
  UZB: "UZ", VIE: "VN", YEM: "YE",
  // Afrique
  ALG: "DZ", ANG: "AO", BDI: "BI", BEN: "BJ", BOT: "BW", BUR: "BF", CAF: "CF",
  CGO: "CG", CIV: "CI", CMR: "CM", COD: "CD", COM: "KM", CPV: "CV", DJI: "DJ",
  EGY: "EG", ERI: "ER", ETH: "ET", GAB: "GA", GAM: "GM", GBS: "GW", GHA: "GH",
  GUI: "GN", KEN: "KE", LBA: "LY", LBR: "LR", LES: "LS", MAD: "MG", MAR: "MA",
  MAW: "MW", MLI: "ML", MOZ: "MZ", MRI: "MU", MTN: "MR", NAM: "NA", NGR: "NG",
  NIG: "NE", RSA: "ZA", RWA: "RW", SEN: "SN", SEY: "SC", SLE: "SL", SOM: "SO",
  STP: "ST", SUD: "SD", SWZ: "SZ", TAN: "TZ", TOG: "TG", TUN: "TN", UGA: "UG",
  ZAM: "ZM", ZIM: "ZW",
  // Oceanie
  AUS: "AU", FIJ: "FJ", NZL: "NZ", PNG: "PG", SAM: "WS", SOL: "SB", TGA: "TO",
  VAN: "VU",
  // Cas particuliers (UK split)
  ENG: "gb-eng",
  SCO: "gb-sct",
  WAL: "gb-wls",
  NIR: "gb-nir",
};


// Composant Flag : affiche le drapeau d'un pays par code 3 lettres
window.Flag = function Flag({ country, width = 36, height = 24, className = "", rounded = true }) {
  if (!country) return null;
  const codeUpper = country.toUpperCase();

  // Si code 2 lettres (genre "FR", "GB", "ES") : on l'utilise directement
  // Sinon on cherche dans le mapping 3-lettres ATP/WTA
  let code2;
  if (codeUpper.length === 2) {
    code2 = codeUpper;  // deja un code ISO 2
  } else {
    code2 = COUNTRY_3_TO_2[codeUpper];
  }

  // Pas trouve : fallback code en texte
  if (!code2) {
    return (
      <span
        className={`flag-text ${className}`}
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          width: `${width}px`,
          height: `${height}px`,
          background: "#374151",
          color: "#fff",
          fontFamily: "Sora, sans-serif",
          fontSize: "9px",
          fontWeight: "bold",
          borderRadius: rounded ? "3px" : "0",
          flexShrink: 0,
        }}
      >
        {codeUpper}
      </span>
    );
  }

  // SVG depuis jsDelivr CDN (lipis/flag-icons)
  // 4x3 = ratio standard officiel
  const url = `https://cdn.jsdelivr.net/gh/lipis/flag-icons/flags/4x3/${code2.toLowerCase()}.svg`;

  return (
    <img
      src={url}
      alt={country}
      title={country}
      className={className}
      style={{
        width: `${width}px`,
        height: `${height}px`,
        objectFit: "cover",
        borderRadius: rounded ? "3px" : "0",
        flexShrink: 0,
        boxShadow: "0 1px 2px rgba(0,0,0,0.3)",
        display: "block",
      }}
      onError={(e) => {
        // Si l'image ne charge pas (offline / CDN bloque), bascule sur texte
        const span = document.createElement("span");
        span.className = `flag-text ${className}`;
        span.style.cssText = `display:inline-flex;align-items:center;justify-content:center;width:${width}px;height:${height}px;background:#374151;color:#fff;font-family:Sora, sans-serif;font-size:9px;font-weight:bold;border-radius:${rounded ? "3px" : "0"};flex-shrink:0;`;
        span.textContent = code3;
        e.target.replaceWith(span);
      }}
    />
  );
};
