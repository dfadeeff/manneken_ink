"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { Gender, Mood, ClothingSelection } from "./clothingData";

interface MannekenState {
  gender: Gender;
  mood: Mood;
  clothes: ClothingSelection;
  isTalking: boolean;
  setGender: (g: Gender) => void;
  setMood: (m: Mood) => void;
  setClothes: (c: ClothingSelection) => void;
  setIsTalking: (t: boolean) => void;
  switchGender: (g: Gender) => void;
}

const MannekenContext = createContext<MannekenState | null>(null);

export function MannekenProvider({ children }: { children: ReactNode }) {
  const [gender, setGender] = useState<Gender>("boy");
  const [mood, setMood] = useState<Mood>("happy");
  const [clothes, setClothes] = useState<ClothingSelection>({
    hat: null, top: null, bottom: null, shoes: null,
  });
  const [isTalking, setIsTalking] = useState(false);

  const switchGender = useCallback((g: Gender) => {
    setGender(g);
    setClothes({ hat: null, top: null, bottom: null, shoes: null });
  }, []);

  return (
    <MannekenContext.Provider
      value={{
        gender, mood, clothes, isTalking,
        setGender, setMood, setClothes, setIsTalking, switchGender,
      }}
    >
      {children}
    </MannekenContext.Provider>
  );
}

export function useManneken() {
  const ctx = useContext(MannekenContext);
  if (!ctx) throw new Error("useManneken must be used within MannekenProvider");
  return ctx;
}