import sqlite3

class Modifydb:
    SCHEMA = '''
            PRAGMA synchronous=FULL;

            CREATE TABLE IF NOT EXISTS main (
            userid integer NOT NULL,
            trackno text NOT NULL UNIQUE,
            timestamp text,
            received text,
            note text
            ); '''

    def __init__(self, db):
        self._db = sqlite3.connect(db, isolation_level=None)
        self._db.executescript(self.SCHEMA)

    def __del__(self):
        self._db.close()

    # adds a row to db
    def insert_data(self, userid, trackno, timestamp, received, note=''):
        try:
            self._db.execute('INSERT INTO main (userid, trackno, timestamp, received, note) VALUES (?,?,?,?,?)', (userid, trackno, timestamp, received, note))
        except sqlite3.IntegrityError:
            # Handle the case when a duplicate trackno is encountered
            # For example, you can update the existing row with the new values
            self._db.execute('UPDATE main SET userid=?, timestamp=?, received=?, note=? WHERE trackno=?', (userid, timestamp, received, note, trackno))

    def select_unreceived(self):
        sql = 'SELECT userid, trackno, timestamp, note FROM main WHERE received = ? ORDER BY userid ASC'
        return self._db.execute(sql, ('no',)).fetchall()

    # modify row as received
    def set_received(self, trackno):
        sql = 'UPDATE main SET received = ? WHERE trackno = ?'
        self._db.execute(sql, ('yes',trackno))

    def update_timestamp(self, timestamp, trackno):
        sql = 'UPDATE main SET timestamp = ? WHERE trackno = ?'
        self._db.execute(sql, (timestamp, trackno))

    def select_by_userid(self, userid):
        sql = 'SELECT trackno,note FROM main WHERE userid = ? AND received = ? ORDER BY timestamp ASC'
        return self._db.execute(sql, (userid,'no')).fetchall()

    def delete_track(self, userid, trackno):
        sql = 'DELETE FROM main where userid = ? AND trackno = ?'
        self._db.execute(sql, (userid,trackno))