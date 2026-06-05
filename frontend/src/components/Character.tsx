"use client";

import { Gender, Mood, ClothingSelection, getClothingItem } from "./clothingData";

interface Props {
  gender: Gender;
  clothes: ClothingSelection;
  mood: Mood;
  isTalking: boolean;
}

function Eyes({ mood }: { mood: Mood }) {
  switch (mood) {
    case "excited":
      return (
        <>
          <text x="82" y="58" fontSize="10" textAnchor="middle">⭐</text>
          <text x="118" y="58" fontSize="10" textAnchor="middle">⭐</text>
        </>
      );
    case "sad":
      return (
        <>
          <ellipse cx="87" cy="55" rx="5" ry="6" fill="#2d3748" />
          <ellipse cx="113" cy="55" rx="5" ry="6" fill="#2d3748" />
          <circle cx="89" cy="53" r="2" fill="white" />
          <circle cx="115" cy="53" r="2" fill="white" />
          {/* tears */}
          <ellipse cx="80" cy="62" rx="2" ry="3" fill="#90cdf4" opacity="0.7" />
          <ellipse cx="120" cy="64" rx="2" ry="3" fill="#90cdf4" opacity="0.7" />
        </>
      );
    case "angry":
      return (
        <>
          <circle cx="87" cy="56" r="5" fill="#2d3748" />
          <circle cx="113" cy="56" r="5" fill="#2d3748" />
          <circle cx="89" cy="54" r="2" fill="white" />
          <circle cx="115" cy="54" r="2" fill="white" />
          {/* angry brows */}
          <line x1="78" y1="43" x2="94" y2="47" stroke="#2d3748" strokeWidth="3" strokeLinecap="round" />
          <line x1="122" y1="43" x2="106" y2="47" stroke="#2d3748" strokeWidth="3" strokeLinecap="round" />
        </>
      );
    case "scared":
      return (
        <>
          <ellipse cx="87" cy="54" rx="6" ry="7" fill="white" stroke="#2d3748" strokeWidth="1.5" />
          <ellipse cx="113" cy="54" rx="6" ry="7" fill="white" stroke="#2d3748" strokeWidth="1.5" />
          <circle cx="87" cy="55" r="3" fill="#2d3748" />
          <circle cx="113" cy="55" r="3" fill="#2d3748" />
        </>
      );
    case "silly":
      return (
        <>
          <line x1="80" y1="55" x2="94" y2="55" stroke="#2d3748" strokeWidth="3" strokeLinecap="round" />
          <circle cx="113" cy="55" r="5" fill="#2d3748" />
          <circle cx="115" cy="53" r="2" fill="white" />
        </>
      );
    case "curious":
      return (
        <>
          <circle cx="87" cy="53" r="5" fill="#2d3748" />
          <circle cx="113" cy="53" r="6" fill="#2d3748" />
          <circle cx="89" cy="51" r="2" fill="white" />
          <circle cx="115" cy="51" r="2.5" fill="white" />
          {/* raised brow */}
          <path d="M 105 42 Q 113 38 121 42" fill="none" stroke="#2d3748" strokeWidth="2.5" strokeLinecap="round" />
        </>
      );
    default: // happy, calm
      return (
        <>
          <circle cx="87" cy="55" r="5" fill="#2d3748" />
          <circle cx="113" cy="55" r="5" fill="#2d3748" />
          <circle cx="89" cy="53" r="2" fill="white" />
          <circle cx="115" cy="53" r="2" fill="white" />
        </>
      );
  }
}

function Mouth({ mood, isTalking }: { mood: Mood; isTalking: boolean }) {
  if (isTalking) {
    return (
      <ellipse cx="100" cy="75" rx="8" ry="6" fill="#e53e3e">
        <animate attributeName="ry" values="6;3;6" dur="0.3s" repeatCount="indefinite" />
      </ellipse>
    );
  }

  switch (mood) {
    case "happy":
    case "calm":
      return <path d="M 90 73 Q 100 83 110 73" fill="none" stroke="#e53e3e" strokeWidth="2" strokeLinecap="round" />;
    case "excited":
      return (
        <>
          <path d="M 88 72 Q 100 86 112 72" fill="#e53e3e" stroke="#c53030" strokeWidth="1" />
          <rect x="92" y="72" width="16" height="3" fill="white" rx="1" />
        </>
      );
    case "sad":
      return <path d="M 90 78 Q 100 70 110 78" fill="none" stroke="#e53e3e" strokeWidth="2" strokeLinecap="round" />;
    case "angry":
      return (
        <path d="M 92 78 Q 100 72 108 78" fill="none" stroke="#e53e3e" strokeWidth="2.5" strokeLinecap="round" />
      );
    case "silly":
      return (
        <>
          <ellipse cx="100" cy="76" rx="10" ry="7" fill="#e53e3e" />
          <ellipse cx="100" cy="80" rx="6" ry="4" fill="#fc8181" />
        </>
      );
    case "scared":
      return <ellipse cx="100" cy="76" rx="5" ry="7" fill="#e53e3e" />;
    case "curious":
      return <ellipse cx="102" cy="76" rx="4" ry="3" fill="#e53e3e" />;
    default:
      return <path d="M 90 73 Q 100 83 110 73" fill="none" stroke="#e53e3e" strokeWidth="2" strokeLinecap="round" />;
  }
}

function HatSVG({ gender, itemId }: { gender: Gender; itemId: string }) {
  const item = getClothingItem(gender, "hat", itemId);
  if (!item) return null;
  const { primary, secondary, accent } = item.colors;

  switch (itemId) {
    case "crown":
    case "tiara":
      return (
        <g>
          <polygon points="72,35 78,15 88,30 100,10 112,30 122,15 128,35" fill={primary} stroke={secondary} strokeWidth="1.5" />
          {accent && <><circle cx="100" cy="22" r="3" fill={accent} /><circle cx="85" cy="28" r="2" fill={accent} /><circle cx="115" cy="28" r="2" fill={accent} /></>}
        </g>
      );
    case "wizard":
      return (
        <g>
          <polygon points="100,0 70,38 130,38" fill={primary} stroke={secondary} strokeWidth="1.5" />
          <rect x="65" y="34" width="70" height="8" rx="3" fill={secondary} />
          {accent && <><text x="100" y="25" fontSize="10" textAnchor="middle" fill={accent}>★</text></>}
        </g>
      );
    case "party":
      return (
        <g>
          <polygon points="100,5 75,38 125,38" fill={primary} stroke={secondary} strokeWidth="1.5" />
          <circle cx="100" cy="5" r="4" fill={accent || "#fefcbf"} />
          <circle cx="90" cy="25" r="2" fill="#faf089" /><circle cx="110" cy="20" r="2" fill="#90cdf4" /><circle cx="105" cy="30" r="2" fill="#68d391" />
        </g>
      );
    case "cowboy":
      return (
        <g>
          <ellipse cx="100" cy="36" rx="48" ry="8" fill={primary} stroke={secondary} strokeWidth="1.5" />
          <rect x="78" y="15" width="44" height="22" rx="10" fill={primary} stroke={secondary} strokeWidth="1.5" />
        </g>
      );
    case "chef":
      return (
        <g>
          <circle cx="85" cy="22" r="14" fill={primary} stroke={secondary} strokeWidth="1" />
          <circle cx="115" cy="22" r="14" fill={primary} stroke={secondary} strokeWidth="1" />
          <circle cx="100" cy="18" r="16" fill={primary} stroke={secondary} strokeWidth="1" />
          <rect x="75" y="30" width="50" height="8" rx="2" fill={primary} stroke={secondary} strokeWidth="1" />
        </g>
      );
    case "helmet":
      return (
        <g>
          <ellipse cx="100" cy="40" rx="38" ry="28" fill={primary} stroke={secondary} strokeWidth="2" />
          <rect x="65" y="40" width="70" height="6" rx="2" fill={secondary} />
          <rect x="90" y="16" width="20" height="6" rx="2" fill="white" />
        </g>
      );
    case "pirate":
      return (
        <g>
          <path d="M 68 38 Q 100 5 132 38" fill={primary} stroke={secondary} strokeWidth="2" />
          <rect x="65" y="34" width="70" height="8" rx="2" fill={secondary} />
          <text x="100" y="30" fontSize="12" textAnchor="middle" fill="white">☠</text>
        </g>
      );
    case "flower_crown":
      return (
        <g>
          <ellipse cx="100" cy="32" rx="32" ry="5" fill="transparent" />
          {[72, 82, 92, 102, 112, 122].map((x, i) => (
            <circle key={i} cx={x} cy={30 + (i % 2) * 3} r="5" fill={[primary, accent || "#fbb6ce", secondary][i % 3]} />
          ))}
          {[77, 87, 97, 107, 117].map((x, i) => (
            <circle key={`l${i}`} cx={x} cy={33} r="3" fill={secondary} />
          ))}
        </g>
      );
    case "detective":
      return (
        <g>
          <ellipse cx="100" cy="36" rx="38" ry="6" fill={primary} stroke={secondary} strokeWidth="1.5" />
          <rect x="78" y="18" width="44" height="20" rx="6" fill={primary} stroke={secondary} strokeWidth="1.5" />
          <rect x="82" y="18" width="36" height="4" rx="2" fill={secondary} />
        </g>
      );
    default: // beanie, cap, tophat
      if (itemId === "tophat") {
        return (
          <g>
            <rect x="78" y="10" width="44" height="28" rx="4" fill={primary} stroke={secondary} strokeWidth="2" />
            <rect x="65" y="35" width="70" height="8" rx="3" fill={secondary} />
          </g>
        );
      }
      if (itemId === "cap") {
        return (
          <g>
            <path d="M 68 38 Q 70 18 100 15 Q 130 18 132 38" fill={primary} stroke={secondary} strokeWidth="2" />
            <rect x="55" y="34" width="50" height="6" rx="2" fill={secondary} />
          </g>
        );
      }
      // beanie
      return (
        <g>
          <path d="M 70 38 Q 70 12 100 10 Q 130 12 130 38" fill={primary} stroke={secondary} strokeWidth="2" />
          <rect x="68" y="34" width="64" height="8" rx="3" fill={secondary} />
          <circle cx="100" cy="10" r="5" fill={primary} />
        </g>
      );
  }
}

function TopSVG({ gender, itemId }: { gender: Gender; itemId: string }) {
  const item = getClothingItem(gender, "top", itemId);
  if (!item) return null;
  const { primary, secondary, accent } = item.colors;

  const isLongSleeve = ["hoodie", "hoodie_f", "jacket", "jacket_f", "sweater", "sweater_f", "cardigan", "suit_jacket"].includes(itemId);
  const hasCape = itemId === "superhero";
  const isGown = itemId === "princess_top";

  return (
    <g>
      {hasCape && (
        <path d="M 75 98 L 50 175 Q 100 185 150 175 L 125 98" fill={primary} opacity="0.7" stroke={secondary} strokeWidth="1" />
      )}
      {isGown && (
        <path d="M 74 155 L 55 230 Q 100 240 145 230 L 126 155" fill={primary} opacity="0.5" stroke={secondary} strokeWidth="1" />
      )}
      <rect x="74" y="94" width="52" height="72" rx="8" fill={primary} stroke={secondary} strokeWidth="2" />
      {isLongSleeve ? (
        <>
          <rect x="54" y="99" width="22" height="50" rx="10" fill={primary} stroke={secondary} strokeWidth="2" />
          <rect x="124" y="99" width="22" height="50" rx="10" fill={primary} stroke={secondary} strokeWidth="2" />
        </>
      ) : (
        <>
          <rect x="54" y="99" width="22" height="30" rx="10" fill={primary} stroke={secondary} strokeWidth="2" />
          <rect x="124" y="99" width="22" height="30" rx="10" fill={primary} stroke={secondary} strokeWidth="2" />
        </>
      )}
      {accent && (
        <>
          <circle cx="100" cy="115" r="3" fill={accent} />
          <circle cx="100" cy="130" r="3" fill={accent} />
          <circle cx="100" cy="145" r="3" fill={accent} />
        </>
      )}
      {itemId === "polo" && <path d="M 90 94 L 100 105 L 110 94" fill="none" stroke={secondary} strokeWidth="2" />}
    </g>
  );
}

function BottomSVG({ gender, itemId }: { gender: Gender; itemId: string }) {
  const item = getClothingItem(gender, "bottom", itemId);
  if (!item) return null;
  const { primary, secondary } = item.colors;

  const isSkirt = ["skirt_pink", "skirt_blue", "tutu", "long_skirt", "plaid_skirt"].includes(itemId);
  const isShorts = ["shorts_blue", "shorts_red", "shorts_f", "bermuda"].includes(itemId);

  if (isSkirt) {
    const skirtLength = itemId === "long_skirt" ? 65 : itemId === "tutu" ? 35 : 45;
    return (
      <g>
        <rect x="73" y="155" width="54" height="14" rx="4" fill={primary} stroke={secondary} strokeWidth="2" />
        <path d={`M 73 165 L 60 ${165 + skirtLength} Q 100 ${170 + skirtLength} 140 ${165 + skirtLength} L 127 165`}
          fill={primary} stroke={secondary} strokeWidth="2" />
        {itemId === "tutu" && (
          <>
            <path d={`M 73 168 L 55 ${175 + skirtLength} Q 100 ${180 + skirtLength} 145 ${175 + skirtLength} L 127 168`}
              fill={primary} opacity="0.4" stroke="none" />
          </>
        )}
        {itemId === "plaid_skirt" && (
          <>
            <line x1="85" y1="165" x2="75" y2="210" stroke={secondary} strokeWidth="2" opacity="0.5" />
            <line x1="100" y1="165" x2="100" y2="210" stroke={secondary} strokeWidth="2" opacity="0.5" />
            <line x1="115" y1="165" x2="125" y2="210" stroke={secondary} strokeWidth="2" opacity="0.5" />
          </>
        )}
      </g>
    );
  }

  const legHeight = isShorts ? 30 : 57;

  return (
    <g>
      <rect x="73" y="155" width="54" height="18" rx="4" fill={primary} stroke={secondary} strokeWidth="2" />
      <rect x="77" y="164" width="20" height={legHeight} rx="8" fill={primary} stroke={secondary} strokeWidth="2" />
      <rect x="103" y="164" width="20" height={legHeight} rx="8" fill={primary} stroke={secondary} strokeWidth="2" />
    </g>
  );
}

function ShoesSVG({ gender, itemId }: { gender: Gender; itemId: string }) {
  const item = getClothingItem(gender, "shoes", itemId);
  if (!item) return null;
  const { primary, secondary, accent } = item.colors;

  const isBoots = ["boots", "rain_boots", "rain_boots_f", "ugg", "hightops"].includes(itemId);

  return (
    <g>
      {isBoots && (
        <>
          <rect x="75" y="210" width="20" height="16" rx="4" fill={primary} stroke={secondary} strokeWidth="1.5" />
          <rect x="107" y="210" width="20" height="16" rx="4" fill={primary} stroke={secondary} strokeWidth="1.5" />
        </>
      )}
      <ellipse cx="85" cy="226" rx="16" ry="10" fill={primary} stroke={secondary} strokeWidth="2" />
      <ellipse cx="115" cy="226" rx="16" ry="10" fill={primary} stroke={secondary} strokeWidth="2" />
      {accent && (
        <>
          <circle cx="85" cy="222" r="2" fill={accent} />
          <circle cx="115" cy="222" r="2" fill={accent} />
        </>
      )}
    </g>
  );
}

export default function Character({ gender, clothes, mood, isTalking }: Props) {
  const skinColor = "#FDBF60";
  const skinStroke = "#e6a540";
  const isGirl = gender === "girl";

  return (
    <svg viewBox="0 0 200 250" className="w-full max-w-[280px] mx-auto">
      {/* Hair (behind head) */}
      {isGirl && (
        <g>
          <ellipse cx="100" cy="55" rx="42" ry="42" fill="#8B4513" />
          <ellipse cx="65" cy="80" rx="10" ry="30" fill="#8B4513" />
          <ellipse cx="135" cy="80" rx="10" ry="30" fill="#8B4513" />
        </g>
      )}

      {/* Head */}
      <circle cx="100" cy="60" r="35" fill={skinColor} stroke={skinStroke} strokeWidth="2" />

      {/* Hair (boy - on top) */}
      {!isGirl && (
        <path d="M 68 52 Q 70 28 100 25 Q 130 28 132 52 Q 120 40 100 42 Q 80 40 68 52" fill="#8B4513" />
      )}

      {/* Eyes */}
      <Eyes mood={mood} />

      {/* Mouth */}
      <Mouth mood={mood} isTalking={isTalking} />

      {/* Cheeks */}
      <circle cx="75" cy="68" r="6" fill="#FEB2B2" opacity="0.5" />
      <circle cx="125" cy="68" r="6" fill="#FEB2B2" opacity="0.5" />

      {/* Hat */}
      {clothes.hat && <HatSVG gender={gender} itemId={clothes.hat} />}

      {/* Body */}
      <rect x="75" y="95" width="50" height="70" rx="8" fill={skinColor} stroke={skinStroke} strokeWidth="2" />

      {/* Arms */}
      <rect x="55" y="100" width="20" height="50" rx="10" fill={skinColor} stroke={skinStroke} strokeWidth="2" />
      <rect x="125" y="100" width="20" height="50" rx="10" fill={skinColor} stroke={skinStroke} strokeWidth="2" />

      {/* Top clothing */}
      {clothes.top && <TopSVG gender={gender} itemId={clothes.top} />}

      {/* Legs */}
      <rect x="78" y="165" width="18" height="55" rx="8" fill={skinColor} stroke={skinStroke} strokeWidth="2" />
      <rect x="104" y="165" width="18" height="55" rx="8" fill={skinColor} stroke={skinStroke} strokeWidth="2" />

      {/* Bottom clothing */}
      {clothes.bottom && <BottomSVG gender={gender} itemId={clothes.bottom} />}

      {/* Feet */}
      <ellipse cx="87" cy="225" rx="14" ry="8" fill={skinColor} stroke={skinStroke} strokeWidth="2" />
      <ellipse cx="113" cy="225" rx="14" ry="8" fill={skinColor} stroke={skinStroke} strokeWidth="2" />

      {/* Shoes */}
      {clothes.shoes && <ShoesSVG gender={gender} itemId={clothes.shoes} />}
    </svg>
  );
}