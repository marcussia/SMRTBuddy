export type Locale = 'en' | 'zh' | 'ms' | 'ta'

export type ScreenId =
  | 'language' | 'profile' | 'plan' | 'listening' | 'recognised' | 'overview'
  | 'guide' | 'wrong-way' | 'sos' | 'recording' | 'family' | 'family-journey'

export const languages: Array<{ id: Locale; label: string; code: string }> = [
  { id: 'en', label: 'English', code: 'EN' },
  { id: 'zh', label: '中文', code: '中' },
  { id: 'ms', label: 'Bahasa Melayu', code: 'BM' },
  { id: 'ta', label: 'தமிழ்', code: 'த' },
]

export const screenLabels: Array<{ id: ScreenId; label: string; group: string }> = [
  { id: 'language', label: 'Language', group: 'Pitch flow' },
  { id: 'profile', label: 'Profile', group: 'Pitch flow' },
  { id: 'plan', label: 'Plan journey', group: 'Pitch flow' },
  { id: 'listening', label: 'Voice destination', group: 'Pitch flow' },
  { id: 'recognised', label: 'Destination recognised', group: 'Pitch flow' },
  { id: 'overview', label: 'Journey overview', group: 'Pitch flow' },
  { id: 'guide', label: 'Direction + SOS', group: 'Pitch flow' },
  { id: 'wrong-way', label: 'Recovery guidance', group: 'Safety' },
  { id: 'sos', label: 'SOS confirmation', group: 'Safety' },
  { id: 'recording', label: 'Audio message', group: 'Safety' },
  { id: 'family', label: 'Family access', group: 'Family demo' },
  { id: 'family-journey', label: 'Shared journey', group: 'Family demo' },
]

export const journeySteps = [
  { number: 1, title: 'Leave home', detail: 'Home in Bedok' },
  { number: 2, title: 'Walk to Bedok MRT', detail: '12 min at your walking pace' },
  { number: 3, title: 'Use the accessible entrance', detail: 'Lift and sheltered path' },
  { number: 4, title: 'Take the East West Line', detail: 'Towards Tuas Link' },
  { number: 5, title: 'Alight at Outram Park', detail: 'Prepare to follow the lift signs' },
  { number: 6, title: 'Follow Exit 7', detail: 'Take the lift towards the yellow 7 sign' },
  { number: 7, title: 'Use the sheltered SGH link', detail: 'Follow the hospital signs' },
  { number: 8, title: 'Arrive at SGH', detail: 'Singapore General Hospital' },
]

export const guideCopy: Record<Locale, { station: string; step: string; title: string; instruction: string; distance: string; ahead: string; status: string; hear: string; lost: string; speechLanguage: string }> = {
  en: { station: 'Outram Park', step: 'Step 6 of 8', title: 'Follow Exit 7', instruction: 'Take the lift towards the yellow Exit 7 sign.', distance: '28 m', ahead: 'ahead', status: 'You’re on the right path', hear: 'Play instruction', lost: 'I’m lost', speechLanguage: 'en-SG' },
  zh: { station: '欧南园', step: '第 6 步，共 8 步', title: '前往 7 号出口', instruction: '搭电梯前往 7 号出口。寻找黄色的 7 号标志。', distance: '28 米', ahead: '前方', status: '您走对了', hear: '播放语音指示', lost: '我迷路了', speechLanguage: 'zh-SG' },
  ms: { station: 'Outram Park', step: 'Langkah 6 daripada 8', title: 'Ikut arah ke Pintu Keluar 7', instruction: 'Naik lif menuju ke Pintu Keluar 7. Cari tanda 7 berwarna kuning.', distance: '28 m', ahead: 'di hadapan', status: 'Anda berada di laluan yang betul', hear: 'Dengar arahan', lost: 'Saya sesat', speechLanguage: 'ms-MY' },
  ta: { station: 'ஊட்ரம் பார்க்', step: 'படி 6 / 8', title: 'வெளியேறும் வழி 7', instruction: 'மின்தூக்கியில் வெளியேறும் வழி 7-க்குச் செல்லுங்கள். மஞ்சள் 7 குறியீட்டைத் தேடுங்கள்.', distance: '28 மீ', ahead: 'முன்னால்', status: 'சரியான வழியில் உள்ளீர்கள்', hear: 'வழிகாட்டலைக் கேட்க', lost: 'வழி தெரியவில்லை', speechLanguage: 'ta-SG' },
}
