export interface Learner {
  id: string;
  name: string;
  school_class: number;
  language: "de" | "en";
  avatar: string;
}

export interface TutorSession {
  id: string;
  learner_id: string;
  subject: string | null;
  topic_id: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intercepted: boolean;
}

export interface Topic {
  id: string;
  subject: string;
  label: string;
}
