/**
 * Couche sémantique au-dessus de Lineicons.
 *
 * Les gabarits ne référencent jamais un nom d'icône brut : ils utilisent
 * `Icons.<intention>`. Changer de style d'icône (ou passer au pack Pro) se fait
 * donc ici uniquement.
 *
 * Limites du pack **gratuit** Lineicons (855 icônes « outlined ») : il ne
 * contient aucune icône `Warning`, `Alert`, `Info`, `QrCode`, `Recycle` ni
 * `Image`. Les substituts retenus sont signalés en commentaire ; le pack Pro
 * (31 204 icônes) permettrait de les obtenir telles quelles.
 */
import {
  ArrowLeftOutlined,
  ArrowRightOutlined,
  BarChart4Outlined,
  BoxArchive1Outlined,
  Buildings1Outlined,
  CalendarDaysOutlined,
  CheckCircle1Outlined,
  CheckOutlined,
  ChevronDownOutlined,
  ChevronRightOutlined,
  Cloud2Outlined,
  CloudDownloadOutlined,
  CloudUploadOutlined,
  DashboardSquare1Outlined,
  DollarCircleOutlined,
  Download1Outlined,
  ExitOutlined,
  EyeOutlined,
  Gear1Outlined,
  Home2Outlined,
  Leaf1Outlined,
  Locked1Outlined,
  MapMarker1Outlined,
  MapPin5Outlined,
  MoonHalfRight5Outlined,
  Pencil1Outlined,
  PlantscaleOutlined,
  PlusOutlined,
  Search1Outlined,
  Shield2Outlined,
  Spinner3Outlined,
  Sun1Outlined,
  Ticket1Outlined,
  Trash3Outlined,
  TruckDelivery1Outlined,
  Upload1Outlined,
  User4Outlined,
  Wallet1Outlined,
  XmarkCircleOutlined,
  XmarkOutlined
} from '@lineiconshq/free-icons'

export const Icons = {
  // Marque & navigation
  brand: Leaf1Outlined,
  home: Home2Outlined,
  map: MapMarker1Outlined,
  dashboard: DashboardSquare1Outlined,
  chart: BarChart4Outlined,
  admin: Gear1Outlined,
  account: User4Outlined,
  add: PlusOutlined,
  logout: ExitOutlined,

  // Thème
  themeLight: Sun1Outlined,
  themeDark: MoonHalfRight5Outlined,

  // Statuts & retours
  success: CheckCircle1Outlined,
  check: CheckOutlined,
  error: XmarkCircleOutlined, // pas d'icône « Warning/Alert » dans le pack gratuit
  close: XmarkOutlined,
  lock: Locked1Outlined,
  shield: Shield2Outlined,
  eye: EyeOutlined,
  loading: Spinner3Outlined,

  // Métier
  location: MapPin5Outlined,
  co2: Cloud2Outlined,
  material: BoxArchive1Outlined,
  money: DollarCircleOutlined,
  wallet: Wallet1Outlined,
  trees: PlantscaleOutlined,
  weighing: Ticket1Outlined,
  calendar: CalendarDaysOutlined,
  organization: Buildings1Outlined,
  transport: TruckDelivery1Outlined,

  // Actions
  search: Search1Outlined,
  edit: Pencil1Outlined,
  delete: Trash3Outlined,
  download: Download1Outlined,
  downloadCloud: CloudDownloadOutlined,
  upload: CloudUploadOutlined,
  uploadSimple: Upload1Outlined,
  previous: ArrowLeftOutlined,
  next: ArrowRightOutlined,
  expand: ChevronDownOutlined,
  collapse: ChevronRightOutlined
} as const

export type IconName = keyof typeof Icons
