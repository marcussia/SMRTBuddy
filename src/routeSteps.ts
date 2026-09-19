import type { Locale } from './data'
import homeLift from './assets/images/step-1-hdb-lift.jpg'
import bedokExterior from './assets/images/step-2-bedok-mrt.jpg'
import bedokExitB from './assets/images/step-3-bedok-exit-b.jpg'
import bedokPlatform from './assets/images/step-4-bedok-platform.jpg'
import outramLift from './assets/images/step-5-outram-lift.jpg'
import exitSeven from './assets/images/outram-exit-7.jpg'
import sghRoute from './assets/images/step-7-sgh-route.svg'
import sghEntrance from './assets/images/step-8-sgh-entrance.jpg'

export type RouteStep = {
  title: string
  instruction: string
  place: string
  distance: string
  image: string
  alt: string
}

const images = [
  { image: homeLift, alt: 'Lift lobby in a Singapore HDB block' },
  { image: bedokExterior, alt: 'Bedok MRT station seen from New Upper Changi Road' },
  { image: bedokExitB, alt: 'The clearly marked Exit B entrance at Bedok MRT station' },
  { image: bedokPlatform, alt: 'Platform at Bedok MRT station on the East West Line' },
  { image: outramLift, alt: 'Lift and wheelchair access area at Outram Park MRT station' },
  { image: exitSeven, alt: 'Yellow Exit 7 sign at Outram Park MRT station' },
  { image: sghRoute, alt: 'High-contrast route diagram from Outram Park Exit 7 to SGH by sheltered walkway' },
  { image: sghEntrance, alt: 'Entrance to Block 4 at Singapore General Hospital' },
] as const

const copy: Record<Locale, Array<Omit<RouteStep, 'image' | 'alt'>>> = {
  en: [
    { title: 'Leave home', instruction: 'Head to the lift lobby and go downstairs.', place: 'Home in Bedok', distance: 'Now' },
    { title: 'Walk to Bedok MRT', instruction: 'Follow the sheltered path towards Bedok MRT.', place: 'Bedok', distance: '620 m' },
    { title: 'Enter Bedok MRT', instruction: 'Use Exit B. After the fare gates, follow the lift signs.', place: 'Bedok MRT', distance: 'Exit B' },
    { title: 'Take the lift to the platform', instruction: 'Board the East West Line towards Tuas Link.', place: 'Bedok MRT', distance: '11 stops' },
    { title: 'Alight at Outram Park', instruction: 'Leave the train and follow the lift signs.', place: 'Outram Park', distance: 'Next stop' },
    { title: 'Follow Exit 7', instruction: 'Take the lift towards the yellow Exit 7 sign.', place: 'Outram Park', distance: '28 m' },
    { title: 'Follow the sheltered walkway', instruction: 'After Exit 7, follow the green SGH signs.', place: 'Outram Park Exit 7', distance: '310 m' },
    { title: 'Arrive at SGH', instruction: 'The hospital entrance is ahead on your left.', place: 'Singapore General Hospital', distance: 'You’re here' },
  ],
  zh: [
    { title: '离开家', instruction: '前往电梯大厅并下楼。', place: '勿洛的家', distance: '现在' }, { title: '步行前往勿洛地铁站', instruction: '沿着有盖通道前往勿洛地铁站。', place: '勿洛', distance: '620 米' },
    { title: '进入勿洛地铁站', instruction: '使用 B 出口。通过闸门后，跟随电梯标志。', place: '勿洛地铁站', distance: 'B 出口' }, { title: '乘电梯到月台', instruction: '乘搭开往大士连路方向的东西线列车。', place: '勿洛地铁站', distance: '11 站' },
    { title: '在欧南园下车', instruction: '下车后跟随电梯标志。', place: '欧南园', distance: '下一站' }, { title: '前往 7 号出口', instruction: '搭电梯前往 7 号出口。寻找黄色的 7 号标志。', place: '欧南园', distance: '28 米' },
    { title: '沿着有盖通道前行', instruction: '离开 7 号出口后，跟随绿色的 SGH 标志。', place: '欧南园 7 号出口', distance: '310 米' }, { title: '抵达 SGH', instruction: '医院入口就在左前方。', place: '新加坡中央医院', distance: '您已抵达' },
  ],
  ms: [
    { title: 'Keluar dari rumah', instruction: 'Pergi ke lobi lif dan turun ke tingkat bawah.', place: 'Rumah di Bedok', distance: 'Sekarang' }, { title: 'Berjalan ke MRT Bedok', instruction: 'Ikut laluan berbumbung menuju ke MRT Bedok.', place: 'Bedok', distance: '620 m' },
    { title: 'Masuk ke MRT Bedok', instruction: 'Gunakan Pintu Keluar B. Selepas pagar tambang, ikut tanda lif.', place: 'MRT Bedok', distance: 'Pintu B' }, { title: 'Naik lif ke platform', instruction: 'Naik Laluan Timur Barat menuju ke Tuas Link.', place: 'MRT Bedok', distance: '11 stesen' },
    { title: 'Turun di Outram Park', instruction: 'Turun dari kereta api dan ikut tanda lif.', place: 'Outram Park', distance: 'Stesen seterusnya' }, { title: 'Ikut arah ke Pintu Keluar 7', instruction: 'Naik lif menuju ke Pintu Keluar 7. Cari tanda 7 berwarna kuning.', place: 'Outram Park', distance: '28 m' },
    { title: 'Ikut laluan berbumbung', instruction: 'Selepas Pintu Keluar 7, ikut tanda SGH berwarna hijau.', place: 'Pintu Keluar 7', distance: '310 m' }, { title: 'Tiba di SGH', instruction: 'Pintu masuk hospital berada di hadapan sebelah kiri.', place: 'Singapore General Hospital', distance: 'Anda sudah tiba' },
  ],
  ta: [
    { title: 'வீட்டிலிருந்து புறப்படுங்கள்', instruction: 'மின்தூக்கி பகுதிக்குச் சென்று கீழே செல்லுங்கள்.', place: 'Bedok வீடு', distance: 'இப்போது' }, { title: 'Bedok MRT-க்கு நடந்து செல்லுங்கள்', instruction: 'மூடிய நடைபாதையைப் பின்பற்றி Bedok MRT-க்குச் செல்லுங்கள்.', place: 'Bedok', distance: '620 மீ' },
    { title: 'Bedok MRT-க்குள் செல்லுங்கள்', instruction: 'வெளியேறும் வழி B-ஐ பயன்படுத்துங்கள். கட்டண வாயிலுக்குப் பிறகு மின்தூக்கி குறியீடுகளைப் பின்பற்றுங்கள்.', place: 'Bedok MRT', distance: 'வழி B' }, { title: 'மின்தூக்கியில் நடைமேடைக்குச் செல்லுங்கள்', instruction: 'Tuas Link நோக்கிச் செல்லும் கிழக்கு மேற்கு பாதை ரயிலில் ஏறுங்கள்.', place: 'Bedok MRT', distance: '11 நிலையங்கள்' },
    { title: 'Outram Park-ல் இறங்குங்கள்', instruction: 'ரயிலிலிருந்து இறங்கி மின்தூக்கி குறியீடுகளைப் பின்பற்றுங்கள்.', place: 'Outram Park', distance: 'அடுத்த நிலையம்' }, { title: 'வெளியேறும் வழி 7', instruction: 'மின்தூக்கியில் வெளியேறும் வழி 7-க்குச் செல்லுங்கள். மஞ்சள் 7 குறியீட்டைத் தேடுங்கள்.', place: 'ஊட்ரம் பார்க்', distance: '28 மீ' },
    { title: 'மூடிய நடைபாதையைப் பின்பற்றுங்கள்', instruction: 'வெளியேறும் வழி 7-க்குப் பிறகு பச்சை SGH குறியீடுகளைப் பின்பற்றுங்கள்.', place: 'வெளியேறும் வழி 7', distance: '310 மீ' }, { title: 'SGH-ஐ அடையுங்கள்', instruction: 'மருத்துவமனை நுழைவாயில் இடது முன்புறத்தில் உள்ளது.', place: 'Singapore General Hospital', distance: 'வந்துவிட்டீர்கள்' },
  ],
}

export function routeSteps(locale: Locale): RouteStep[] {
  return copy[locale].map((step, index) => ({ ...step, ...images[index] }))
}
