import { Link } from 'react-router-dom'
import Icon from './ui/Icon'

export default function BackLink({ to, children = 'Back' }) {
  return (
    <Link to={to} className="back-link">
      <Icon name="arrowLeft" size={15} />
      {children}
    </Link>
  )
}
