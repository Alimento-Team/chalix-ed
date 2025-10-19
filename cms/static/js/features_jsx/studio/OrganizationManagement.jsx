import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

function OrganizationManagement({ apiUrl, isAdmin }) {
  const [orgs, setOrgs] = useState([]);
  const [newOrgName, setNewOrgName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAdmin) {
      fetch(apiUrl, { credentials: 'include' })
        .then(res => {
          if (!res.ok) throw new Error('Failed to load organizations');
          return res.json();
        })
        .then(data => setOrgs(data))
        .catch(() => setError('Failed to load organizations'));
    }
  }, [apiUrl, isAdmin]);

  const handleCreateOrg = (e) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;
    setLoading(true);
    setError('');
    // Read CSRF token from cookies (Django default)
    const getCookie = (name) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
    };
    const csrftoken = getCookie('csrftoken');

    fetch(apiUrl, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
        'Accept': 'application/json',
      },
      body: JSON.stringify({ name: newOrgName })
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to create organization');
        return res.json();
      })
      .then(org => {
        setOrgs([...orgs, org]);
        setNewOrgName('');
      })
      .catch(() => setError('Failed to create organization'))
      .finally(() => setLoading(false));
  };

  if (!isAdmin) return null;

  return (
    <div className="org-management">
      <form onSubmit={handleCreateOrg}>
        <input
          type="text"
          value={newOrgName}
          onChange={e => setNewOrgName(e.target.value)}
          placeholder="Tên cơ quan"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !newOrgName.trim()}>
          Tạo cơ quan
        </button>
      </form>
      {error && <div className="error">{error}</div>}
      <h3>Danh sách cơ quan</h3>
      <ul>
        {orgs.map(org => (
          <li key={org.id}>{org.name}</li>
        ))}
      </ul>
    </div>
  );
}

OrganizationManagement.propTypes = {
  apiUrl: PropTypes.string.isRequired,
  isAdmin: PropTypes.bool.isRequired,
};

export default OrganizationManagement;
