import api from './axios';

export const listPosts = (page = 1, pageSize = 20, query = '') =>
  api.get('/admin/posts', {
    params: {
      page,
      page_size: pageSize,
      q: query?.trim() || undefined,
    },
  });

export const deletePost = (postId) =>
  api.delete(`/admin/posts/${postId}`);

export const listPostComments = (postId, page = 1, pageSize = 20) =>
  api.get(`/admin/posts/${postId}/comments`, {
    params: { page, page_size: pageSize },
  });

export const deleteComment = (commentId) =>
  api.delete(`/admin/comments/${commentId}`);
