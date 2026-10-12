import './styles.css';
import { Director } from './director';
import { state } from './state';

const app = document.getElementById('app')!;
const director = new Director(app);
director.start();

// 开发调试用：在控制台查看状态与流程
if (import.meta.env.DEV) Object.assign(window, { __game: { director, state } });
