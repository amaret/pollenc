<?php

class MongoStore {

  private static $dbh = false;

  function __construct() {

    if (!self::$dbh) {
    	global $__MONGO_HOST;
    	$m = new Mongo($__MONGO_HOST .':'. '27017');
        self::$dbh = $m->selectDB('wind');
    }
  }

  public function update($collection, $criteria, $data) {
    return self::$dbh->selectCollection($collection)->update($criteria, $data);
  }    
    
  public function remove($collection, $criteria) {
    return self::$dbh->selectCollection($collection)->remove($criteria);
  }
    
  public function save($collection, $data) {
    return self::$dbh->selectCollection($collection)->save($data);
  }
    
  public function findOne($collection, $criteria, $fields = array()) {
    return self::$dbh->selectCollection($collection)->findOne($criteria, $fields);
  }
    
  public function find($collection, $criteria, $fields = array()) {
    return self::$dbh->selectCollection($collection)->find($criteria, $fields);
  }

  public function count($collection, $criteria) {
    return self::$dbh->selectCollection($collection)->count($criteria);
  }
    
  public function newObjectId() {
    return new MongoId();
  }

}

?>
