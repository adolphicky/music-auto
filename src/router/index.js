import { createRouter, createWebHistory } from 'vue-router'
import SearchComponent from '../components/SearchComponent.vue'
import PlaylistSearchComponent from '../components/PlaylistSearchComponent.vue'
import ArtistDownloadComponent from '../components/ArtistDownloadComponent.vue'
import HotPlaylistsComponent from '../components/HotPlaylistsComponent.vue'
import TaskManagerComponent from '../components/TaskManagerComponent.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/search'
  },
  {
    path: '/search',
    name: 'Search',
    component: SearchComponent
  },
  {
    path: '/playlist-download',
    name: 'PlaylistDownload',
    component: PlaylistSearchComponent
  },
  {
    path: '/artist-download',
    name: 'ArtistDownload',
    component: ArtistDownloadComponent
  },
  {
    path: '/hot-playlists',
    name: 'HotPlaylists',
    component: HotPlaylistsComponent
  },
  {
    path: '/task-manager',
    name: 'TaskManager',
    component: TaskManagerComponent
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
