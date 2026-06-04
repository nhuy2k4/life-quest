import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  FiChevronLeft,
  FiChevronRight,
  FiMessageSquare,
  FiSearch,
  FiTrash2,
} from 'react-icons/fi';
import Modal from '../components/Modal';
import { deleteComment, deletePost, listPostComments, listPosts } from '../api/posts';

const PAGE_SIZE = 20;
const COMMENT_PAGE_SIZE = 12;

export default function PostsPage() {
  const [posts, setPosts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [deleteModal, setDeleteModal] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const [commentModal, setCommentModal] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentTotal, setCommentTotal] = useState(0);
  const [commentPage, setCommentPage] = useState(1);
  const [commentLoading, setCommentLoading] = useState(false);

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const commentTotalPages = Math.ceil(commentTotal / COMMENT_PAGE_SIZE);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setQuery(search.trim());
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [search]);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listPosts(page, PAGE_SIZE, query);
      setPosts(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch {
      showToast('Failed to load posts', 'error');
    } finally {
      setLoading(false);
    }
  }, [page, query]);

  useEffect(() => { fetchPosts(); }, [fetchPosts]);

  const filteredPosts = useMemo(() => posts, [posts]);

  const openComments = (post) => {
    setCommentModal(post);
    setCommentPage(1);
  };

  const closeComments = () => {
    setCommentModal(null);
    setComments([]);
    setCommentTotal(0);
  };

  const fetchComments = useCallback(async () => {
    if (!commentModal) return;
    setCommentLoading(true);
    try {
      const res = await listPostComments(commentModal.id, commentPage, COMMENT_PAGE_SIZE);
      setComments(res.data.items || []);
      setCommentTotal(res.data.total || 0);
    } catch {
      showToast('Failed to load comments', 'error');
    } finally {
      setCommentLoading(false);
    }
  }, [commentModal, commentPage]);

  useEffect(() => { fetchComments(); }, [fetchComments]);

  const handleDeletePost = async () => {
    if (!deleteModal) return;
    setActionLoading(true);
    try {
      await deletePost(deleteModal.id);
      showToast('Post deleted');
      setDeleteModal(null);
      fetchPosts();
    } catch {
      showToast('Failed to delete post', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteComment = async (commentId) => {
    const ok = window.confirm('Delete this comment?');
    if (!ok) return;
    try {
      await deleteComment(commentId);
      showToast('Comment deleted');
      fetchComments();
    } catch {
      showToast('Failed to delete comment', 'error');
    }
  };

  const formatDate = (value) => {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleString();
  };

  return (
    <div className="page">
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      <div className="page-header">
        <div>
          <h1 className="page-title">Post Management</h1>
          <p className="page-subtitle">{total} posts in the system</p>
        </div>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            id="post-search"
            type="text"
            placeholder="Search by caption, username, location..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="card table-card">
        {loading ? (
          <div className="loading-center"><span className="spinner"></span></div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <colgroup>
                <col style={{ width: '32%' }} />
                <col style={{ width: '16%' }} />
                <col style={{ width: '15%' }} />
                <col style={{ width: '10%' }} />
                <col style={{ width: '17%' }} />
                <col style={{ width: '10%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Post</th>
                  <th>Author</th>
                  <th>Quest</th>
                  <th>Interactions</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredPosts.map((post) => (
                  <tr key={post.id}>
                    <td>
                      <div className="post-cell">
                        <div className="post-thumb">
                          {post.media_url ? (
                            <img src={post.media_url} alt="" />
                          ) : (
                            <div className="post-thumb-placeholder">No Image</div>
                          )}
                        </div>
                        <div className="post-meta" style={{ minWidth: 0 }}>
                          <div className="fw-600 text-truncate">
                            {post.caption || '(no caption)'}
                          </div>
                          <div className="text-muted text-sm text-truncate">
                            {post.location_name || 'No location'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="user-cell">
                        <div className="avatar">
                          {(post.user?.username || '?')[0].toUpperCase()}
                        </div>
                        <div style={{ minWidth: 0 }}>
                          <div className="fw-600 text-truncate">@{post.user?.username || 'unknown'}</div>
                          <div className="text-muted text-sm">LV {post.user?.level_id ?? '-'}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="text-sm" style={{ minWidth: 0 }}>
                        <div className="fw-600 text-truncate">{post.quest_title || '-'}</div>
                        <div className="text-muted">{post.quest_id ? 'With quest' : 'Free'}</div>
                      </div>
                    </td>
                    <td>
                      <div className="text-sm">
                        <div>❤️ {post.like_count || 0}</div>
                        <div>💬 {post.comment_count || 0}</div>
                      </div>
                    </td>
                    <td className="text-muted">{formatDate(post.created_at)}</td>
                    <td>
                      <div className="action-btns">
                        <button
                          id={`view-comments-${post.id}`}
                          className="icon-btn icon-btn-primary"
                          title="View comments"
                          onClick={() => openComments(post)}
                        >
                          <FiMessageSquare size={15} />
                        </button>
                        <button
                          id={`delete-post-${post.id}`}
                          className="icon-btn icon-btn-danger"
                          title="Delete post"
                          onClick={() => setDeleteModal(post)}
                        >
                          <FiTrash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredPosts.length === 0 && (
                  <tr><td colSpan={6} className="empty-row">No posts found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="pagination">
        <button className="page-btn" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
          <FiChevronLeft />
        </button>
        <span className="page-info">Page {page} / {totalPages || 1}</span>
        <button className="page-btn" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
          <FiChevronRight />
        </button>
      </div>

      {deleteModal && (
        <Modal onClose={() => setDeleteModal(null)}>
          <div className="modal-icon">🗑️</div>
          <h3 className="modal-title">Delete Post</h3>
          <p className="modal-desc">
            Are you sure you want to delete this post? This action cannot be undone.
          </p>
          <div className="modal-actions">
            <button className="btn-secondary" onClick={() => setDeleteModal(null)}>Cancel</button>
            <button className="btn-danger" onClick={handleDeletePost} disabled={actionLoading}>
              {actionLoading ? <span className="spinner-sm" /> : 'Delete'}
            </button>
          </div>
        </Modal>
      )}

      {commentModal && (
        <Modal onClose={closeComments} wide>
          <h3 className="modal-title">Post Comments</h3>
          <p className="modal-desc">@{commentModal.user?.username || 'unknown'}</p>

          <div className="card table-card">
            {commentLoading ? (
              <div className="loading-center"><span className="spinner"></span></div>
            ) : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Author</th>
                      <th>Content</th>
                      <th>Date</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {comments.map((comment) => (
                      <tr key={comment.id}>
                        <td>
                          <div className="user-cell">
                            <div className="avatar">
                              {(comment.user?.username || '?')[0].toUpperCase()}
                            </div>
                            <div className="fw-600">@{comment.user?.username || 'unknown'}</div>
                          </div>
                        </td>
                        <td>
                          <div className="comment-body">
                            {comment.is_deleted ? <em>Deleted</em> : comment.content}
                          </div>
                        </td>
                        <td className="text-muted">{formatDate(comment.created_at)}</td>
                        <td>
                          <button
                            className="icon-btn icon-btn-danger"
                            title="Delete comment"
                            onClick={() => handleDeleteComment(comment.id)}
                          >
                            <FiTrash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {comments.length === 0 && (
                      <tr><td colSpan={4} className="empty-row">No comments</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="pagination" style={{ marginTop: 12 }}>
            <button
              className="page-btn"
              disabled={commentPage <= 1}
              onClick={() => setCommentPage(p => p - 1)}
            >
              <FiChevronLeft />
            </button>
            <span className="page-info">Page {commentPage} / {commentTotalPages || 1}</span>
            <button
              className="page-btn"
              disabled={commentPage >= commentTotalPages}
              onClick={() => setCommentPage(p => p + 1)}
            >
              <FiChevronRight />
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
